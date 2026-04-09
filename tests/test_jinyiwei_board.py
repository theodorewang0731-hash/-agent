from apps.api.routes.dashboard import jinyiwei_board
from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry


def setup_function() -> None:
    case_registry.reset()


def test_jinyiwei_board_reports_internal_issue_and_repair_advice() -> None:
    case = case_registry.create_case(
        title="依赖污染修复",
        content="检测并修复 executor_pool 中的依赖污染",
        priority="critical",
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case["case_id"])
    orchestrator.submit_for_approval(case["case_id"])
    orchestrator.approve_case(case["case_id"])
    orchestrator.mark_repair_pending(case["case_id"], reason="dependency corruption")
    orchestrator.authorize_repair(
        case_id=case["case_id"],
        strategy="patch_then_rerun",
        reason="critical dependency issue",
        scope="executor_pool/api_builder",
    )

    payload = jinyiwei_board()
    assert payload["counts"]["issues_total"] == 1
    assert payload["counts"]["critical"] == 1
    issue = payload["items"][0]
    assert issue["severity"] == "critical"
    assert issue["repair_strategy"] == "patch_then_rerun"
    assert issue["repair_scope"] == "executor_pool/api_builder"
    assert "repair.authorized" in issue["evidence_topics"]
