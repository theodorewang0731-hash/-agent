from apps.api.routes.dashboard import jinyiwei_board
from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry


def setup_function() -> None:
    case_registry.reset()


def _create_running_case(*, title: str, content: str, priority: str) -> dict:
    case = case_registry.create_case(
        title=title,
        content=content,
        priority=priority,
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case["case_id"])
    orchestrator.submit_for_approval(case["case_id"])
    orchestrator.approve_case(case["case_id"])
    return case


def test_jinyiwei_board_tracks_issue_level_stage_and_disposition_authority() -> None:
    user_decision_case = _create_running_case(
        title="依赖污染修复",
        content="检测并修复 executor_pool 中的依赖污染",
        priority="critical",
    )
    orchestrator.mark_repair_pending(
        user_decision_case["case_id"],
        reason="dependency corruption",
        risk_level="critical",
        affected_stage="执行",
        affected_step="executor_pool/api_builder",
        auto_handle_allowed=False,
    )

    auto_handled_case = _create_running_case(
        title="导出看板补齐",
        content="修复导出流程中缺少双看板文件的问题",
        priority="normal",
    )
    orchestrator.mark_repair_pending(
        auto_handled_case["case_id"],
        reason="dashboard export missing",
        risk_level="low",
        affected_stage="执行",
        affected_step="dual_dashboard_export",
        auto_handle_allowed=True,
    )
    orchestrator.auto_handle_repair(
        case_id=auto_handled_case["case_id"],
        strategy="export_dual_dashboards_then_rerun",
        reason="low-risk output gap",
        scope="runtime/hpc_exports",
        risk_level="low",
        affected_stage="执行",
        affected_step="dual_dashboard_export",
    )

    payload = jinyiwei_board()
    assert payload["counts"]["issues_total"] == 2
    assert payload["counts"]["critical"] == 1
    assert payload["counts"]["auto_handled"] == 1
    assert payload["counts"]["pending_user_decision"] == 1

    issues = {item["case_id"]: item for item in payload["items"]}

    critical_issue = issues[user_decision_case["case_id"]]
    assert critical_issue["severity"] == "critical"
    assert critical_issue["risk_level"] == "critical"
    assert critical_issue["affected_stage"] == "执行"
    assert critical_issue["affected_step"] == "executor_pool/api_builder"
    assert critical_issue["decision_authority"] == "none"
    assert critical_issue["requires_user_order"] is True
    assert critical_issue["handling_mode"] == "user"
    assert critical_issue["audited_stages"] == ["建档", "票拟", "审批", "执行", "修复 / 归档"]
    assert critical_issue["process_trace"][-1] == "repair_pending"
    assert "repair.report.generated" in critical_issue["evidence_topics"]

    auto_issue = issues[auto_handled_case["case_id"]]
    assert auto_issue["severity"] == "low"
    assert auto_issue["repair_strategy"] == "export_dual_dashboards_then_rerun"
    assert auto_issue["repair_scope"] == "runtime/hpc_exports"
    assert auto_issue["decision_authority"] == "jinyiwei.advisor"
    assert auto_issue["requires_user_order"] is False
    assert auto_issue["handling_mode"] == "auto"
    assert auto_issue["audited_stages"] == ["建档", "票拟", "审批", "执行", "修复 / 归档", "执行"]
    assert auto_issue["process_trace"][-1] == "executing"
    assert "repair.auto_handled" in auto_issue["evidence_topics"]
