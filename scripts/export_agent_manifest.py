import json
from pathlib import Path

from core.registry.agents import governance_agent_registry


def export_manifest(output_path: str = "agents.json") -> str:
    target = Path(output_path)
    agents = governance_agent_registry.list_agents()
    manifest = []
    for agent in agents:
        manifest.append(
            {
                "id": agent["agent_id"],
                "name": agent["display_name"],
                "department": agent["department"],
                "style": agent["style_id"],
                "workspace": f"runtime/workspaces/{agent['workspace_slug']}",
                "soulPath": agent["soul_path"],
                "implemented": agent["implemented"],
                "supportedModelSources": agent["supported_model_sources"],
                "localModelSizeLimit": agent["local_model_size_limit"],
                "subagents": {"allowAgents": agent.get("allowed_targets", [])},
            }
        )

    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


if __name__ == "__main__":
    path = export_manifest()
    print(f"Agent manifest exported to {path}")
