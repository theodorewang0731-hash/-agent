import json
from pathlib import Path

from core.registry.cases import case_registry


def export_case_timeline(case_id: str, output_dir: str = "data/audit") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timeline = case_registry.get_timeline(case_id)

    output_path = Path(output_dir) / f"{case_id}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(timeline, file, ensure_ascii=False, indent=2)

    return str(output_path)
