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


def _status_from_case(case: dict, has_repair_auth: bool, has_rerun: bool) -> str:
    if case["state"] == "repair_pending":
        return "待受令"
    if case["state"] == "repair_authorized":
        return "已授权"
    if case["state"] == "rerunning":
        return "重跑中"
    if case["state"] in {"failed", "frozen"}:
        return "阻断中"
    if has_rerun and case["state"] in {"executing", "reporting", "archived"}:
        return "已处置"
    if has_repair_auth:
        return "观察中"
    return "未处置"


def _extract_jinyiwei_issue(case: dict) -> dict | None:
    timeline = case_registry.get_timeline(case["case_id"])
    repair_report = next((event for event in reversed(timeline) if event["topic"] == "repair.report.generated"), None)
    repair_authorized = next((event for event in reversed(timeline) if event["topic"] == "repair.authorized"), None)
    rerun_event = next((event for event in reversed(timeline) if event["topic"] == "repair.rerun.completed"), None)
    failed_event = next((event for event in reversed(timeline) if event["topic"] == "case.state.failed"), None)

    if not any([repair_report, repair_authorized, rerun_event, failed_event]) and case["state"] not in {
        "repair_pending",
        "repair_authorized",
        "rerunning",
        "failed",
        "frozen",
    }:
        return None

    latest_issue_event = repair_authorized or repair_report or failed_event or rerun_event
    detected_reason = None
    if repair_report:
        detected_reason = repair_report["payload"].get("reason")
    elif failed_event:
        detected_reason = "执行阶段进入 failed"
    elif case["state"] == "frozen":
        detected_reason = "案件被冻结，等待进一步处置"

    repair_strategy = repair_authorized["payload"].get("strategy") if repair_authorized else "待锦衣卫建议"
    repair_scope = repair_authorized["payload"].get("scope") if repair_authorized else "待确认"
    recommendation = {
        "repair_pending": "等待用户正式下达修复令，再进入重跑。",
        "repair_authorized": "按已授权策略执行修复，并持续记录证据链。",
        "rerunning": "观察重跑结果，确认问题是否真正解除。",
        "failed": "优先冻结风险扩散，再补齐定位和影响分析。",
        "frozen": "维持冻结，等待用户决定 patch / rollback / rerun。",
    }.get(case["state"], "继续观察执行结果，并准备归档修复结论。")

    evidence_topics = [
        event["topic"]
        for event in timeline
        if event["topic"].startswith("repair.") or event["topic"].startswith("case.state.")
    ][-6:]

    return {
        "issue_id": f"{case['case_id']}:jinyiwei",
        "case_id": case["case_id"],
        "case_title": case["title"],
        "current_state": case["state"],
        "severity": _severity_from_case(case),
        "status": _status_from_case(
            case,
            has_repair_auth=repair_authorized is not None,
            has_rerun=rerun_event is not None,
        ),
        "detected_by": "jinyiwei",
        "summary": detected_reason or "检测到内部问题，需要锦衣卫持续跟踪。",
        "repair_strategy": repair_strategy,
        "repair_scope": repair_scope,
        "recommendation": recommendation,
        "evidence_topics": evidence_topics,
        "updated_at": latest_issue_event["timestamp"] if latest_issue_event else case["updated_at"],
    }


@router.get("/dashboard/jinyiwei-board")
def jinyiwei_board() -> dict:
    cases = case_registry.list_cases()
    items = [issue for case in cases if (issue := _extract_jinyiwei_issue(case)) is not None]
    severity_counts = Counter(item["severity"] for item in items)
    status_counts = Counter(item["status"] for item in items)

    items.sort(key=lambda item: (item["updated_at"], item["case_id"]), reverse=True)
    return {
        "counts": {
            "issues_total": len(items),
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
        },
        "issues_by_severity": dict(sorted(severity_counts.items())),
        "issues_by_status": dict(sorted(status_counts.items())),
        "items": items,
    }
