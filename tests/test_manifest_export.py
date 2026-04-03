import json
from pathlib import Path

from scripts.export_agent_manifest import export_manifest


def test_export_agent_manifest_contains_18_agents(tmp_path: Path) -> None:
    output = tmp_path / "agents.json"
    export_manifest(str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 18
    assert payload[0]["supportedModelSources"] == [
        "remote_api",
        "local_distilled",
        "local_full",
    ]
