from collections import Counter

from fastapi import APIRouter

from core.registry.agents import governance_agent_registry
from core.registry.cases import case_registry

router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary() -> dict:
    cases = case_registry.list_cases()
    agents = governance_agent_registry.list_agents()
    state_counts = Counter(case["state"] for case in cases)
    department_counts = Counter(agent["department"] for agent in agents)

    return {
        "counts": {
            "cases_total": len(cases),
            "agents_total": len(agents),
            "agents_implemented": sum(1 for agent in agents if agent["implemented"]),
        },
        "cases_by_state": dict(sorted(state_counts.items())),
        "agents_by_department": dict(sorted(department_counts.items())),
        "recent_cases": cases[:5],
    }


STAGE_LABELS = {
    "created": "建档",
    "accepted": "建档",
    "planning": "票拟",
    "internal_review": "票拟",
    "submitted_for_approval": "审批",
    "approved": "审批",
    "rejected": "审批",
    "escalated": "审批",
    "dispatched": "执行",
    "executing": "执行",
    "rerunning": "执行",
    "reporting": "执行",
    "repair_pending": "修复 / 归档",
    "repair_authorized": "修复 / 归档",
    "paused": "修复 / 归档",
    "frozen": "修复 / 归档",
    "failed": "修复 / 归档",
    "archived": "修复 / 归档",
    "cancelled": "修复 / 归档",
}

RISK_LEVELS = {"low", "medium", "high", "critical"}


def _severity_from_case(case: dict) -> str:
    base = {
        "low": "low",
        "normal": "medium",
        "medium": "medium",
        "high": "high",
        "critical": "critical",
    }.get(case["priority"], "medium")
    if case["state"] in {"failed", "frozen"} and base in {"low", "medium"}:
        return "high"
    return base


def _normalize_risk_level(raw_value: object, default: str) -> str:
    risk_level = str(raw_value or default).lower()
    return risk_level if risk_level in RISK_LEVELS else default


def _extract_process_trace(timeline: list[dict]) -> list[str]:
    trace = ["created"]
    for event in timeline:
        if event["topic"].startswith("case.state."):
            payload = event.get("payload", {})
            state = str(payload.get("to") or event["topic"].split("case.state.", 1)[1])
            trace.append(state)
    return trace


def _extract_audited_stages(process_trace: list[str]) -> list[str]:
    stages: list[str] = []
    for state in process_trace:
        stage = STAGE_LABELS.get(state, "待定位")
        if not stages or stages[-1] != stage:
            stages.append(stage)
    return stages


def _infer_stage_from_event(event: dict, fallback_state: str) -> str:
    payload = event.get("payload", {})
    if payload.get("affected_stage"):
        return str(payload["affected_stage"])
    if event["topic"].startswith("case.state."):
        state = str(payload.get("to") or event["topic"].split("case.state.", 1)[1])
        return STAGE_LABELS.get(state, "待定位")
    if event["topic"].startswith("case.planning"):
        return "票拟"
    if event["topic"].startswith("execution."):
        return "执行"
    if event["topic"].startswith("repair."):
        return STAGE_LABELS.get(fallback_state, "修复 / 归档")
    return STAGE_LABELS.get(fallback_state, "待定位")


def _build_issue_status(*, requires_user_order: bool, decision_authority: str, has_rerun: bool, current_state: str) -> str:
    if decision_authority == "jinyiwei.advisor":
        if has_rerun and current_state in {"executing", "reporting", "archived"}:
            return "已自行处理"
        return "锦衣卫处理中"
    if requires_user_order and decision_authority == "imperial_user":
        if has_rerun and current_state in {"executing", "reporting", "archived"}:
            return "已按用户决策处置"
        return "待执行用户决策"
    if requires_user_order:
        return "待用户决定"
    return "持续观察中"


def _build_issue_recommendation(*, requires_user_order: bool, decision_authority: str, risk_level: str) -> str:
    if decision_authority == "jinyiwei.advisor":
        return "低风险问题已由锦衣卫汇报并自行处置，保留证据链供复核。"
    if requires_user_order or risk_level in {"high", "critical"}:
        return "问题等级较高，保留处置权给用户，由用户决定 patch / rollback / rerun / freeze。"
    return "可由锦衣卫先行处理，再向用户回奏处置结果。"


def _extract_jinyiwei_issues(case: dict) -> list[dict]:
    timeline = case_registry.get_timeline(case["case_id"])
    if not timeline:
        return []

    base_severity = _severity_from_case(case)
    process_trace = _extract_process_trace(timeline)
    audited_stages = _extract_audited_stages(process_trace)
    report_events = [event for event in timeline if event["topic"] == "repair.report.generated"]
    if not report_events:
        fallback_event = next(
            (event for event in reversed(timeline) if event["topic"] in {"case.state.failed", "case.state.frozen"}),
            None,
        )
        if fallback_event is None and case["state"] not in {"failed", "frozen", "repair_pending", "repair_authorized", "rerunning"}:
            return []
        report_events = [
            {
                "event_id": f"{case['case_id']}:fallback",
                "topic": "repair.report.generated",
                "producer": "jinyiwei.advisor",
                "timestamp": fallback_event["timestamp"] if fallback_event else case["updated_at"],
                "payload": {
                    "reason": "检测到流程异常，需由锦衣卫补充定位与影响分析。",
                    "risk_level": base_severity,
                    "affected_stage": STAGE_LABELS.get(case["state"], "待定位"),
                    "affected_step": case["state"],
                    "auto_handle_allowed": base_severity in {"low", "medium"},
                },
            }
        ]

    issues: list[dict] = []
    for index, report_event in enumerate(report_events, start=1):
        report_payload = report_event.get("payload", {})
        report_offset = timeline.index(report_event) if report_event in timeline else max(len(timeline) - 1, 0)
        trailing_timeline = timeline[report_offset:]

        repair_authorized = next((event for event in trailing_timeline if event["topic"] == "repair.authorized"), None)
        auto_handled = next((event for event in trailing_timeline if event["topic"] == "repair.auto_handled"), None)
        rerun_event = next((event for event in trailing_timeline if event["topic"] == "repair.rerun.completed"), None)

        risk_level = _normalize_risk_level(report_payload.get("risk_level"), base_severity)
        auto_handle_allowed = report_payload.get("auto_handle_allowed")
        requires_user_order = not bool(auto_handle_allowed) if auto_handle_allowed is not None else risk_level in {"high", "critical"}
        decision_authority = "none"
        if auto_handled or (repair_authorized and repair_authorized["producer"] == "jinyiwei.advisor"):
            decision_authority = "jinyiwei.advisor"
        elif repair_authorized:
            decision_authority = "imperial_user"

        latest_issue_event = rerun_event or auto_handled or repair_authorized or report_event
        repair_payload = repair_authorized.get("payload", {}) if repair_authorized else {}
        affected_stage = (
            report_payload.get("affected_stage")
            or repair_payload.get("affected_stage")
            or _infer_stage_from_event(report_event, case["state"])
        )
        affected_step = (
            report_payload.get("affected_step")
            or repair_payload.get("affected_step")
            or repair_payload.get("scope")
            or case["state"]
        )
        repair_scope = repair_payload.get("scope") or str(affected_step)
        repair_strategy = repair_payload.get("strategy") if repair_authorized else "待锦衣卫建议"
        evidence_topics = [
            event["topic"]
            for event in trailing_timeline
            if event["topic"].startswith("repair.")
            or event["topic"].startswith("case.state.")
            or event["topic"].startswith("execution.")
        ][:8]

        issues.append(
            {
                "issue_id": report_event.get("event_id", f"{case['case_id']}:jinyiwei:{index}"),
                "case_id": case["case_id"],
                "case_title": case["title"],
                "current_state": case["state"],
                "severity": risk_level,
                "risk_level": risk_level,
                "status": _build_issue_status(
                    requires_user_order=requires_user_order,
                    decision_authority=decision_authority,
                    has_rerun=rerun_event is not None,
                    current_state=case["state"],
                ),
                "detected_by": report_event["producer"],
                "summary": str(report_payload.get("reason") or "检测到内部问题，需要锦衣卫持续跟踪。"),
                "repair_strategy": str(repair_strategy),
                "repair_scope": str(repair_scope),
                "recommendation": _build_issue_recommendation(
                    requires_user_order=requires_user_order,
                    decision_authority=decision_authority,
                    risk_level=risk_level,
                ),
                "affected_stage": str(affected_stage),
                "affected_step": str(affected_step),
                "requires_user_order": requires_user_order,
                "decision_authority": decision_authority,
                "handling_mode": "auto" if decision_authority == "jinyiwei.advisor" else "user" if requires_user_order else "observe",
                "process_trace": process_trace,
                "audited_stages": audited_stages,
                "evidence_topics": evidence_topics,
                "updated_at": latest_issue_event["timestamp"],
            }
        )
    return issues


@router.get("/dashboard/jinyiwei-board")
def jinyiwei_board() -> dict:
    cases = case_registry.list_cases()
    items = [issue for case in cases for issue in _extract_jinyiwei_issues(case)]
    severity_counts = Counter(item["severity"] for item in items)
    status_counts = Counter(item["status"] for item in items)
    handling_counts = Counter(item["handling_mode"] for item in items)

    items.sort(key=lambda item: (item["updated_at"], item["case_id"]), reverse=True)
    return {
        "counts": {
            "issues_total": len(items),
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "auto_handled": handling_counts.get("auto", 0),
            "pending_user_decision": sum(1 for item in items if item["requires_user_order"] and item["decision_authority"] == "none"),
        },
        "issues_by_severity": dict(sorted(severity_counts.items())),
        "issues_by_status": dict(sorted(status_counts.items())),
        "issues_by_handling_mode": dict(sorted(handling_counts.items())),
        "items": items,
    }
