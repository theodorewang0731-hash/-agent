import pytest

from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry
from core.state_machine.guards import InvalidTransitionError


def setup_function() -> None:
    case_registry.reset()


def test_case_progression_reaches_executing() -> None:
    case = case_registry.create_case(
        title="demo",
        content="demo",
        priority="normal",
        submitted_by="imperial_user",
    )

    orchestrator.accept_case(case["case_id"])
    assert case_registry.get_case(case["case_id"])["state"] == "planning"

    orchestrator.submit_for_approval(case["case_id"])
    assert case_registry.get_case(case["case_id"])["state"] == "submitted_for_approval"

    orchestrator.approve_case(case["case_id"])
    current = case_registry.get_case(case["case_id"])
    assert current["state"] == "executing"
    assert current["created_at"]
    assert current["updated_at"]


def test_pause_and_resume_only_work_for_running_case() -> None:
    case = case_registry.create_case(
        title="demo",
        content="demo",
        priority="normal",
        submitted_by="imperial_user",
    )

    with pytest.raises(InvalidTransitionError):
        orchestrator.pause_case(case["case_id"])

    orchestrator.accept_case(case["case_id"])
    orchestrator.submit_for_approval(case["case_id"])
    orchestrator.approve_case(case["case_id"])
    orchestrator.pause_case(case["case_id"])

    paused = case_registry.get_case(case["case_id"])
    assert paused["state"] == "paused"
    assert paused["metadata"]["last_active_state"] == "executing"

    orchestrator.resume_case(case["case_id"])
    assert case_registry.get_case(case["case_id"])["state"] == "executing"


def test_timeline_records_repair_authorization() -> None:
    case = case_registry.create_case(
        title="demo",
        content="demo",
        priority="high",
        submitted_by="imperial_user",
    )

    orchestrator.accept_case(case["case_id"])
    orchestrator.submit_for_approval(case["case_id"])
    orchestrator.approve_case(case["case_id"])
    orchestrator.mark_repair_pending(
        case["case_id"],
        reason="dependency corruption",
        risk_level="high",
        affected_stage="执行",
        affected_step="executor_pool/api_builder",
        auto_handle_allowed=False,
    )
    orchestrator.authorize_repair(
        case_id=case["case_id"],
        strategy="patch_then_rerun",
        reason="high risk issue",
        scope="executor_pool/api_builder",
        risk_level="high",
        affected_stage="执行",
        affected_step="executor_pool/api_builder",
    )

    timeline = case_registry.get_timeline(case["case_id"])
    topics = [event["topic"] for event in timeline]
    assert "repair.report.generated" in topics
    assert "repair.authorized" in topics

    report_event = next(event for event in timeline if event["topic"] == "repair.report.generated")
    assert report_event["payload"]["risk_level"] == "high"
    assert report_event["payload"]["affected_stage"] == "执行"
    assert report_event["payload"]["affected_step"] == "executor_pool/api_builder"
    assert report_event["payload"]["auto_handle_allowed"] is False

    repair_event = next(event for event in timeline if event["topic"] == "repair.authorized")
    assert repair_event["producer"] == "imperial_user"
    assert repair_event["payload"]["risk_level"] == "high"
    assert repair_event["payload"]["affected_stage"] == "执行"
    assert repair_event["payload"]["affected_step"] == "executor_pool/api_builder"


def test_auto_handle_repair_records_jinyiwei_authority_and_rerun_requestor() -> None:
    case = case_registry.create_case(
        title="demo",
        content="demo",
        priority="normal",
        submitted_by="imperial_user",
    )

    orchestrator.accept_case(case["case_id"])
    orchestrator.submit_for_approval(case["case_id"])
    orchestrator.approve_case(case["case_id"])
    orchestrator.mark_repair_pending(
        case["case_id"],
        reason="missing export artifact",
        risk_level="low",
        affected_stage="执行",
        affected_step="dual_dashboard_export",
        auto_handle_allowed=True,
    )
    orchestrator.auto_handle_repair(
        case_id=case["case_id"],
        strategy="export_dual_dashboards_then_rerun",
        reason="low risk export gap",
        scope="runtime/hpc_exports",
        risk_level="low",
        affected_stage="执行",
        affected_step="dual_dashboard_export",
    )

    timeline = case_registry.get_timeline(case["case_id"])
    topics = [event["topic"] for event in timeline]
    assert "repair.auto_handled" in topics
    assert "repair.rerun.started" in topics
    assert "repair.rerun.completed" in topics

    auto_event = next(event for event in timeline if event["topic"] == "repair.auto_handled")
    assert auto_event["producer"] == "jinyiwei.advisor"
    assert auto_event["payload"]["risk_level"] == "low"

    rerun_started = next(event for event in timeline if event["topic"] == "repair.rerun.started")
    rerun_completed = next(event for event in timeline if event["topic"] == "repair.rerun.completed")
    assert rerun_started["payload"]["requested_by"] == "jinyiwei.advisor"
    assert rerun_completed["payload"]["requested_by"] == "jinyiwei.advisor"
