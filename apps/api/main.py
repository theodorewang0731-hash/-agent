import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes import agents, cases, dashboard, models
from core.registry.cases import case_registry

app = FastAPI(
    title="RegentOS API",
    version="0.1.0",
    description="Governance-first multi-agent prototype",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api", tags=["cases"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(models.router, prefix="/api", tags=["models"])


@app.on_event("startup")
def load_demo_snapshot() -> None:
    snapshot_path = Path("data/demo_cases.json")
    if case_registry.list_cases() or not snapshot_path.exists():
        return
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    case_registry.load_snapshot(payload, replace=True)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "regentos-api"}
