from apps.api.routes.dashboard import dashboard_summary
from core.orchestrator.engine import orchestrator
from core.registry.cases import case_registry


def setup_function() -> None:
    case_registry.reset()


def test_dashboard_summary_reports_case_and_agent_counts() -> None:
    case = case_registry.create_case(
        title="demo",
        content="demo",
        priority="normal",
        submitted_by="imperial_user",
    )
    orchestrator.accept_case(case["case_id"])

    summary = dashboard_summary()
    assert summary["counts"]["cases_total"] == 1
    assert summary["counts"]["agents_total"] == 18
    assert summary["counts"]["agents_implemented"] == 18
    assert "planning" in summary["cases_by_state"]
