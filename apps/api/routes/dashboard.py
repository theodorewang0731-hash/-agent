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
