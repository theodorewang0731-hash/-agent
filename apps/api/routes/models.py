from fastapi import APIRouter

from core.registry.agents import governance_agent_registry

router = APIRouter()


@router.get("/models/runtime-capabilities")
def runtime_capabilities() -> dict:
    return governance_agent_registry.model_runtime_capabilities()
