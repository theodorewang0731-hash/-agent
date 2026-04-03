from fastapi import APIRouter, HTTPException, Query

from core.registry.agents import governance_agent_registry

router = APIRouter()


@router.get("/agents")
def list_agents(
    department: str | None = Query(default=None),
    style_id: str | None = Query(default=None),
    implemented_only: bool = Query(default=False),
) -> dict:
    return {
        "items": governance_agent_registry.list_agents(
            department=department,
            style_id=style_id,
            implemented_only=implemented_only,
        )
    }


@router.get("/agents/styles")
def list_agent_styles() -> dict:
    return {"items": governance_agent_registry.list_styles()}


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = governance_agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
