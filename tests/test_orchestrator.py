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
    orchestrator.mark_repair_pending(case["case_id"], reason="dependency corruption")
    orchestrator.authorize_repair(
        case_id=case["case_id"],
        strategy="patch_then_rerun",
        reason="high risk issue",
        scope="executor_pool/api_builder",
    )

    topics = [event["topic"] for event in case_registry.get_timeline(case["case_id"])]
    assert "repair.report.generated" in topics
    assert "repair.authorized" in topics
