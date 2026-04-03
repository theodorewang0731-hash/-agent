from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry


def setup_function() -> None:
    case_registry.reset()


def test_snapshot_roundtrip_preserves_cases_and_events() -> None:
    case = case_registry.create_case(
        title="demo",
        content="demo",
        priority="high",
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case["case_id"])
    snapshot = case_registry.export_snapshot()

    case_registry.reset()
    case_registry.load_snapshot(snapshot)

    restored = case_registry.get_case(case["case_id"])
    assert restored is not None
    assert restored["state"] == "planning"
    assert len(case_registry.get_timeline(case["case_id"])) >= 3
