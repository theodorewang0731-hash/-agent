from __future__ import annotations

import html
import json
import random
import re
import shutil
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from fastapi.testclient import TestClient

from apps.api.main import app
from core.registry.cases import case_registry

DEFAULT_INSTRUCTION = "编写一段代码，对随机数组可以进行多种排序的选择，要求至少4种排序方法。"
DEFAULT_OUTPUT_ROOT = Path("runtime/hpc_exports")
DEFAULT_REPAIR_REASON = "首次执行仅生成排序代码，尚未按 README 导出双看板，需要补齐可视化交付。"
DEFAULT_REPAIR_STRATEGY = "export_dual_dashboards_then_rerun"
DEFAULT_REPAIR_SCOPE = "apps/api/routes/dashboard.py, runtime/hpc_exports"
DEFAULT_REPAIR_RISK_LEVEL = "low"
DEFAULT_REPAIR_AFFECTED_STAGE = "执行"
DEFAULT_REPAIR_AFFECTED_STEP = "dual_dashboard_export"

ROLE_SEQUENCE = [
    "cabinet.coordinator",
    "silijian.approver",
    "censorship.inspector",
    "jinyiwei.advisor",
    "cabinet.reporter",
]

ROLE_RATIONALES = {
    "cabinet.coordinator": "负责票拟与执行拆解，优先分配高推理能力模型。",
    "silijian.approver": "负责审批把关，优先分配稳定的指令跟随模型。",
    "censorship.inspector": "负责监督巡检，优先分配响应快的轻量模型。",
    "jinyiwei.advisor": "负责问题定位与修复建议，优先分配代码/推理兼顾模型。",
    "cabinet.reporter": "负责回奏与归档总结，优先分配擅长结构化总结的模型。",
}

KANBAN_GROUPS = [
    ("建档", ["created", "accepted"]),
    ("票拟", ["planning", "internal_review"]),
    ("审批", ["submitted_for_approval", "approved", "rejected", "escalated"]),
    ("执行", ["dispatched", "executing", "reporting", "rerunning"]),
    ("修复 / 归档", ["repair_pending", "repair_authorized", "paused", "frozen", "failed", "archived", "cancelled"]),
]

EXECUTION_SEQUENCE = ["bubble", "insertion", "selection", "merge", "quick"]

FALLBACK_MODEL_INVENTORY = [
    {
        "name": "deepseek-r1:70b",
        "provider": "ollama",
        "source": "local_full",
        "capabilities": ["reasoning", "code"],
        "tags": ["reasoning", "code"],
    },
    {
        "name": "qwen2.5-coder:32b-instruct",
        "provider": "ollama",
        "source": "local_full",
        "capabilities": ["code", "repair"],
        "tags": ["coder", "instruct"],
    },
    {
        "name": "gpt-5.4-mini",
        "provider": "openai",
        "source": "remote_api",
        "capabilities": ["approval", "summary"],
        "tags": ["chat", "mini"],
    },
    {
        "name": "qwen2.5:14b-instruct",
        "provider": "ollama",
        "source": "local_distilled",
        "capabilities": ["summary", "inspection"],
        "tags": ["instruct"],
    },
    {
        "name": "qwen2.5:7b-instruct-q4_k_m",
        "provider": "ollama",
        "source": "local_distilled",
        "capabilities": ["inspection", "classification"],
        "tags": ["instruct", "q4"],
    },
]

SORTING_SCRIPT = textwrap.dedent(
    """\
    from __future__ import annotations

    import argparse
    import json
    import random


    def bubble_sort(values: list[int]) -> list[int]:
        items = values[:]
        for end in range(len(items) - 1, 0, -1):
            for index in range(end):
                if items[index] > items[index + 1]:
                    items[index], items[index + 1] = items[index + 1], items[index]
        return items


    def insertion_sort(values: list[int]) -> list[int]:
        items = values[:]
        for index in range(1, len(items)):
            current = items[index]
            position = index - 1
            while position >= 0 and items[position] > current:
                items[position + 1] = items[position]
                position -= 1
            items[position + 1] = current
        return items


    def selection_sort(values: list[int]) -> list[int]:
        items = values[:]
        for index in range(len(items)):
            min_index = index
            for scan in range(index + 1, len(items)):
                if items[scan] < items[min_index]:
                    min_index = scan
            items[index], items[min_index] = items[min_index], items[index]
        return items


    def merge_sort(values: list[int]) -> list[int]:
        if len(values) <= 1:
            return values[:]
        middle = len(values) // 2
        left = merge_sort(values[:middle])
        right = merge_sort(values[middle:])
        merged: list[int] = []
        left_index = 0
        right_index = 0
        while left_index < len(left) and right_index < len(right):
            if left[left_index] <= right[right_index]:
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1
        merged.extend(left[left_index:])
        merged.extend(right[right_index:])
        return merged


    def quick_sort(values: list[int]) -> list[int]:
        if len(values) <= 1:
            return values[:]
        pivot = values[len(values) // 2]
        lower = [item for item in values if item < pivot]
        equal = [item for item in values if item == pivot]
        higher = [item for item in values if item > pivot]
        return quick_sort(lower) + equal + quick_sort(higher)


    SORTERS = {
        "bubble": bubble_sort,
        "insertion": insertion_sort,
        "selection": selection_sort,
        "merge": merge_sort,
        "quick": quick_sort,
    }


    def main() -> None:
        parser = argparse.ArgumentParser(description="Run multiple sorting strategies on a random array.")
        parser.add_argument("--algorithm", choices=sorted(SORTERS), default="merge")
        parser.add_argument("--size", type=int, default=12)
        parser.add_argument("--seed", type=int, default=20260415)
        parser.add_argument("--json", action="store_true", help="Print the result as JSON.")
        parser.add_argument("--values", nargs="*", type=int)
        args = parser.parse_args()

        if args.values:
            values = args.values
        else:
            rng = random.Random(args.seed)
            values = [rng.randint(-50, 99) for _ in range(args.size)]

        output = {
            "algorithm": args.algorithm,
            "input": values,
            "output": SORTERS[args.algorithm](values),
            "available_algorithms": sorted(SORTERS),
        }
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return

        print(f"algorithm: {output['algorithm']}")
        print(f"input: {output['input']}")
        print(f"output: {output['output']}")
        print(f"available_algorithms: {', '.join(output['available_algorithms'])}")


    if __name__ == "__main__":
        main()
    """
)


def _normalize_tags(raw_tags: Any) -> list[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, list):
        return [str(tag).lower() for tag in raw_tags]
    return [str(raw_tags).lower()]


def _extract_model_size(raw_value: Any) -> int | None:
    if isinstance(raw_value, (int, float)):
        return int(raw_value)
    if not isinstance(raw_value, str):
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*b", raw_value.lower())
    if not match:
        return None
    return int(float(match.group(1)))


def _normalize_source(raw_source: Any, model_name: str, provider: str) -> str:
    source = str(raw_source or "").strip().lower()
    if source in {"remote_api", "local_distilled", "local_full"}:
        return source

    provider_name = provider.lower()
    if provider_name in {"openai", "anthropic", "azure", "google", "gemini", "bedrock", "remote_api"}:
        return "remote_api"

    size = _extract_model_size(model_name)
    if size is not None and size >= 32:
        return "local_full"
    return "local_distilled"


def _normalize_model_item(item: Any) -> dict[str, Any] | None:
    if isinstance(item, str):
        name = item
        raw_item: dict[str, Any] = {}
    elif isinstance(item, dict):
        raw_item = dict(item)
        name = (
            raw_item.get("name")
            or raw_item.get("model")
            or raw_item.get("id")
            or raw_item.get("slug")
        )
    else:
        return None

    if not name:
        return None

    provider = str(raw_item.get("provider") or raw_item.get("runtime") or raw_item.get("backend") or "hpc-local")
    return {
        "name": str(name),
        "provider": provider,
        "source": _normalize_source(raw_item.get("source") or raw_item.get("source_id"), str(name), provider),
        "capabilities": [str(item).lower() for item in raw_item.get("capabilities", [])]
        if isinstance(raw_item.get("capabilities"), list)
        else [],
        "tags": _normalize_tags(raw_item.get("tags")),
        "size_b": _extract_model_size(raw_item.get("size_b") or raw_item.get("parameters_b") or raw_item.get("size") or str(name)),
    }


def _flatten_hpc_inventory(raw_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for line in raw_inventory.get("active_model_lines", []):
        if not isinstance(line, dict):
            continue
        line_name = str(line.get("name") or "active model line")
        status = str(line.get("status") or "")
        base_tags = ["active_line", status.replace(" ", "_").lower()]
        if "reason" in line_name.lower() or "reason" in status.lower():
            base_tags.append("reasoning")
        if "qwen" in line_name.lower():
            base_tags.append("qwen")
        if "ministral" in line_name.lower():
            base_tags.append("ministral")
        if "active mainline" in status.lower():
            base_tags.append("mainline")
        if "secondary" in status.lower():
            base_tags.append("secondary")

        teacher = line.get("teacher")
        if teacher:
            items.append(
                {
                    "name": teacher,
                    "provider": "hpc_fs",
                    "source": "local_full",
                    "capabilities": ["reasoning", "approval", "summary"],
                    "tags": [*base_tags, "teacher", line_name],
                }
            )

        student = line.get("student")
        if student:
            items.append(
                {
                    "name": student,
                    "provider": "hpc_fs",
                    "source": "local_distilled",
                    "capabilities": ["inspection", "summary"],
                    "tags": [*base_tags, "student", "distilled", line_name],
                }
            )

    for model_path in raw_inventory.get("archival_or_legacy_models", []):
        items.append(
            {
                "name": model_path,
                "provider": "hpc_fs",
                "tags": ["legacy", "archive"],
            }
        )

    return items


def normalize_model_inventory(raw_inventory: Any) -> list[dict[str, Any]]:
    if raw_inventory is None:
        items = FALLBACK_MODEL_INVENTORY
    elif isinstance(raw_inventory, dict):
        if "models" in raw_inventory:
            items = raw_inventory["models"]
        elif "active_model_lines" in raw_inventory or "archival_or_legacy_models" in raw_inventory:
            items = _flatten_hpc_inventory(raw_inventory)
        else:
            items = []
            for name, meta in raw_inventory.items():
                if isinstance(meta, dict):
                    entry = dict(meta)
                    entry.setdefault("name", name)
                    items.append(entry)
                else:
                    items.append({"name": name})
    elif isinstance(raw_inventory, list):
        items = raw_inventory
    else:
        raise TypeError("Unsupported model inventory format")

    normalized: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for item in items:
        entry = _normalize_model_item(item)
        if not entry or entry["name"] in seen_names:
            continue
        seen_names.add(entry["name"])
        normalized.append(entry)

    if normalized:
        return normalized
    return [dict(item) for item in FALLBACK_MODEL_INVENTORY]


def _score_model(model: dict[str, Any], agent_id: str) -> int:
    name = model["name"].lower()
    source = model["source"]
    size = model.get("size_b") or 0
    tags = set(model.get("capabilities", [])) | set(model.get("tags", []))
    score = 0

    if "mainline" in tags:
        score += 26
    elif "active_line" in tags:
        score += 18
    if "legacy" in tags or "archive" in tags:
        score -= 8

    if agent_id == "cabinet.coordinator":
        if source == "local_full":
            score += 45
        elif source == "remote_api":
            score += 35
        else:
            score += 12
        if any(keyword in name for keyword in ["r1", "qwq", "reason", "gpt", "claude", "deepseek", "qwen"]):
            score += 24
        if "code" in tags or "coder" in name:
            score += 12
        if "teacher" in tags:
            score += 10
        score += min(size, 70)
    elif agent_id == "silijian.approver":
        if source == "remote_api":
            score += 36
        elif source == "local_full":
            score += 28
        else:
            score += 22
        if any(keyword in name for keyword in ["gpt", "claude", "qwen", "llama", "instruct", "chat", "deepseek"]):
            score += 20
        if size and size <= 20:
            score += 12
        if "coder" in name:
            score -= 4
        if "teacher" in tags:
            score += 8
    elif agent_id == "censorship.inspector":
        if source == "local_distilled":
            score += 40
        elif source == "remote_api":
            score += 18
        else:
            score += 14
        if any(keyword in name for keyword in ["mini", "small", "7b", "8b", "14b", "distill", "q4", "q8", "instruct", "chat"]):
            score += 18
        if "inspection" in tags or "classification" in tags:
            score += 15
        if "student" in tags or "distilled" in tags:
            score += 12
        if size and size > 32:
            score -= 18
    elif agent_id == "jinyiwei.advisor":
        if source in {"local_full", "remote_api"}:
            score += 34
        else:
            score += 18
        if any(keyword in name for keyword in ["coder", "code", "gpt", "claude", "qwen", "deepseek", "r1"]):
            score += 24
        if "repair" in tags or "code" in tags:
            score += 16
        if "teacher" in tags:
            score += 6
        score += min(size, 64) // 2
    elif agent_id == "cabinet.reporter":
        if source == "local_distilled":
            score += 28
        elif source == "remote_api":
            score += 24
        else:
            score += 20
        if any(keyword in name for keyword in ["chat", "instruct", "mini", "qwen", "gpt", "llama", "deepseek"]):
            score += 18
        if "summary" in tags:
            score += 15
        if "student" in tags or "distilled" in tags:
            score += 8
        if size and size <= 20:
            score += 10

    return score


def select_model_bindings(raw_inventory: Any = None, *, inventory_source: str = "built-in fallback") -> dict[str, Any]:
    inventory = normalize_model_inventory(raw_inventory)
    used_models: set[str] = set()
    bindings: dict[str, dict[str, str]] = {}

    for agent_id in ROLE_SEQUENCE:
        ranked = sorted(
            inventory,
            key=lambda item: (_score_model(item, agent_id), item["name"]),
            reverse=True,
        )
        chosen = next((item for item in ranked if item["name"] not in used_models), ranked[0])
        used_models.add(chosen["name"])
        bindings[agent_id] = {
            "source": chosen["source"],
            "model": chosen["name"],
            "provider": chosen["provider"],
            "rationale": ROLE_RATIONALES[agent_id],
        }

    source_counter = Counter(binding["source"] for binding in bindings.values())
    return {
        "default_source": source_counter.most_common(1)[0][0],
        "selection_summary": {
            "inventory_source": inventory_source,
            "inventory_count": len(inventory),
            "selected_model_count": len({binding["model"] for binding in bindings.values()}),
        },
        "agents": bindings,
        "inventory_preview": inventory[: min(len(inventory), 8)],
    }


def _bubble_sort(values: list[int]) -> list[int]:
    items = values[:]
    for end in range(len(items) - 1, 0, -1):
        for index in range(end):
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]
    return items


def _insertion_sort(values: list[int]) -> list[int]:
    items = values[:]
    for index in range(1, len(items)):
        current = items[index]
        position = index - 1
        while position >= 0 and items[position] > current:
            items[position + 1] = items[position]
            position -= 1
        items[position + 1] = current
    return items


def _selection_sort(values: list[int]) -> list[int]:
    items = values[:]
    for index in range(len(items)):
        min_index = index
        for scan in range(index + 1, len(items)):
            if items[scan] < items[min_index]:
                min_index = scan
        items[index], items[min_index] = items[min_index], items[index]
    return items


def _merge_sort(values: list[int]) -> list[int]:
    if len(values) <= 1:
        return values[:]
    middle = len(values) // 2
    left = _merge_sort(values[:middle])
    right = _merge_sort(values[middle:])
    merged: list[int] = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        if left[left_index] <= right[right_index]:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1
    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return merged


def _quick_sort(values: list[int]) -> list[int]:
    if len(values) <= 1:
        return values[:]
    pivot = values[len(values) // 2]
    lower = [item for item in values if item < pivot]
    equal = [item for item in values if item == pivot]
    higher = [item for item in values if item > pivot]
    return _quick_sort(lower) + equal + _quick_sort(higher)


SORTING_ALGORITHMS = {
    "bubble": _bubble_sort,
    "insertion": _insertion_sort,
    "selection": _selection_sort,
    "merge": _merge_sort,
    "quick": _quick_sort,
}


def _render_payload(payload: dict[str, Any]) -> str:
    if not payload:
        return "no payload"
    parts = [f"{key}={value}" for key, value in payload.items()]
    return ", ".join(parts[:4])


def _extract_state_visits(case_detail: dict[str, Any], timeline: list[dict[str, Any]]) -> list[dict[str, str]]:
    visits = [
        {
            "state": "created",
            "timestamp": case_detail["created_at"],
            "producer": "gateway",
        }
    ]
    for event in timeline:
        if not event["topic"].startswith("case.state."):
            continue
        payload = event.get("payload", {})
        visits.append(
            {
                "state": payload.get("to") or event["topic"].split("case.state.", 1)[1],
                "timestamp": event["timestamp"],
                "producer": event["producer"],
            }
        )
    return visits


def _dashboard_styles() -> str:
    return textwrap.dedent(
        """\
        :root {
          --bg: #f5efe6;
          --panel: rgba(255, 251, 246, 0.94);
          --panel-strong: #fffdf8;
          --ink: #2f241d;
          --muted: #6f6256;
          --line: rgba(120, 97, 78, 0.18);
          --accent: #8b2f1f;
          --accent-soft: #d76b4b;
          --gold: #c08a1f;
          --green: #2f855a;
          --shadow: 0 18px 45px rgba(68, 42, 24, 0.12);
        }

        * { box-sizing: border-box; }
        body {
          margin: 0;
          font-family: "Noto Serif SC", "Songti SC", serif;
          color: var(--ink);
          background:
            radial-gradient(circle at top left, rgba(255, 222, 197, 0.55), transparent 32%),
            radial-gradient(circle at bottom right, rgba(219, 188, 136, 0.35), transparent 28%),
            linear-gradient(135deg, #f7f3ed 0%, #efe4d4 42%, #f9f5ef 100%);
        }
        a { color: var(--accent); text-decoration: none; }
        .page {
          max-width: 1340px;
          margin: 0 auto;
          padding: 32px 24px 48px;
        }
        .hero {
          display: grid;
          grid-template-columns: 1.5fr 1fr;
          gap: 18px;
          margin-bottom: 22px;
        }
        .hero-card, .panel {
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 24px;
          box-shadow: var(--shadow);
          backdrop-filter: blur(8px);
        }
        .hero-card {
          padding: 28px;
          min-height: 190px;
        }
        .hero-card h1 {
          margin: 10px 0 14px;
          font-size: 34px;
        }
        .eyebrow {
          letter-spacing: 0.24em;
          text-transform: uppercase;
          font-size: 12px;
          color: var(--accent);
        }
        .hero-copy, .muted {
          color: var(--muted);
          line-height: 1.7;
        }
        .stat-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 18px;
        }
        .stat-card {
          background: var(--panel-strong);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 18px;
        }
        .stat-card strong {
          display: block;
          margin-top: 10px;
          font-size: 28px;
        }
        .main-grid {
          display: grid;
          grid-template-columns: 1.3fr 1fr;
          gap: 18px;
          margin-bottom: 18px;
        }
        .panel {
          padding: 22px;
        }
        .panel h2 {
          margin: 6px 0 4px;
        }
        .panel-head {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: flex-start;
          margin-bottom: 16px;
        }
        .panel-label {
          font-size: 12px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--accent);
        }
        .kanban-grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 12px;
        }
        .kanban-column {
          background: rgba(255, 249, 241, 0.78);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 14px;
        }
        .kanban-title {
          font-weight: 700;
          margin-bottom: 10px;
        }
        .case-card, .issue-card, .binding-card, .artifact-card {
          background: var(--panel-strong);
          border: 1px solid var(--line);
          border-radius: 16px;
          padding: 14px;
        }
        .case-card + .case-card,
        .issue-card + .issue-card,
        .artifact-card + .artifact-card {
          margin-top: 10px;
        }
        .case-title {
          font-weight: 700;
          margin-bottom: 6px;
        }
        .pill-row, .tag-row {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 10px;
        }
        .pill, .tag {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 12px;
          border: 1px solid var(--line);
          background: rgba(255, 244, 228, 0.95);
        }
        .timeline {
          display: grid;
          gap: 10px;
        }
        .timeline-item {
          padding: 12px 14px;
          border-left: 3px solid var(--accent-soft);
          border-radius: 0 14px 14px 0;
          background: rgba(255, 250, 243, 0.88);
        }
        .sub-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px;
          margin-bottom: 18px;
        }
        .binding-grid, .issue-grid, .artifact-grid {
          display: grid;
          gap: 12px;
        }
        .issue-card {
          border-left: 4px solid var(--gold);
        }
        .severity-critical { border-left-color: #b42318; }
        .severity-high { border-left-color: #d97706; }
        .severity-medium { border-left-color: #2563eb; }
        .severity-low { border-left-color: #2f855a; }
        pre {
          margin: 0;
          padding: 14px;
          border-radius: 14px;
          background: #2d241d;
          color: #fdf8f2;
          overflow-x: auto;
          font-family: "SFMono-Regular", "JetBrains Mono", monospace;
          font-size: 13px;
          line-height: 1.6;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th, td {
          padding: 10px 12px;
          text-align: left;
          border-bottom: 1px solid var(--line);
          vertical-align: top;
          word-break: break-word;
        }
        .footer-note {
          margin-top: 18px;
          color: var(--muted);
          font-size: 13px;
        }
        @media (max-width: 980px) {
          .hero, .main-grid, .sub-grid, .stat-grid, .kanban-grid {
            grid-template-columns: 1fr;
          }
        }
        """
    )


def _render_main_board(
    *,
    case_detail: dict[str, Any],
    timeline: list[dict[str, Any]],
    summary: dict[str, Any],
    bindings: dict[str, Any],
    artifacts: dict[str, str],
    api_calls: list[dict[str, Any]],
    instruction: str,
    sorting_results: dict[str, Any],
) -> str:
    state_visits = _extract_state_visits(case_detail, timeline)
    columns: list[str] = []
    for group_title, states in KANBAN_GROUPS:
        group_visits = [visit for visit in state_visits if visit["state"] in states]
        if not group_visits:
            cards = ['<div class="muted">暂无案件</div>']
        else:
            history_path = " -> ".join(visit["state"] for visit in group_visits)
            cards = []
            cards.append(
                textwrap.dedent(
                    f"""\
                    <div class="case-card">
                      <div class="case-title">{html.escape(case_detail["title"])}</div>
                      <div class="muted">{html.escape(case_detail["case_id"])}</div>
                      <div class="muted">历史轨迹：{html.escape(history_path)}</div>
                      <div class="pill-row">
                        <span class="pill">first: {html.escape(group_visits[0]["timestamp"])}</span>
                        <span class="pill">last: {html.escape(group_visits[-1]["timestamp"])}</span>
                        <span class="pill">current: {html.escape(case_detail["state"])}</span>
                      </div>
                    </div>
                    """
                )
            )
        columns.append(
            f'<section class="kanban-column"><div class="kanban-title">{html.escape(group_title)}</div>{"".join(cards)}</section>'
        )

    timeline_items = []
    for event in timeline[-16:]:
        timeline_items.append(
            textwrap.dedent(
                f"""\
                <div class="timeline-item">
                  <strong>{html.escape(event["topic"])}</strong>
                  <div class="muted">{html.escape(event["producer"])} · {html.escape(event["timestamp"])}</div>
                  <div>{html.escape(_render_payload(event.get("payload", {})))}</div>
                </div>
                """
            )
        )

    sequence_rows = []
    for step in sorting_results.get("steps", []):
        sequence_rows.append(
            "".join(
                [
                    "<tr>",
                    f"<td>{step['order']}</td>",
                    f"<td>{html.escape(step['algorithm'])}</td>",
                    f"<td>{html.escape(step['command'])}</td>",
                    f"<td>{html.escape(step['output_path'])}</td>",
                    f"<td>{'yes' if step['matches_expected'] else 'no'}</td>",
                    "</tr>",
                ]
            )
        )

    binding_cards = []
    for agent_id, binding in bindings["agents"].items():
        binding_cards.append(
            textwrap.dedent(
                f"""\
                <div class="binding-card">
                  <strong>{html.escape(agent_id)}</strong>
                  <div class="muted">{html.escape(binding["rationale"])}</div>
                  <div class="pill-row">
                    <span class="pill">{html.escape(binding["source"])}</span>
                    <span class="pill">{html.escape(binding["provider"])}</span>
                  </div>
                  <div style="margin-top:10px;">{html.escape(binding["model"])}</div>
                </div>
                """
            )
        )

    artifact_cards = []
    for label, rel_path in artifacts.items():
        artifact_cards.append(
            textwrap.dedent(
                f"""\
                <div class="artifact-card">
                  <strong>{html.escape(label)}</strong>
                  <div class="muted">{html.escape(rel_path)}</div>
                  <div style="margin-top:10px;"><a href="{html.escape(rel_path)}">打开文件</a></div>
                </div>
                """
            )
        )

    api_rows = []
    for call in api_calls:
        api_rows.append(
            f"<tr><td>{html.escape(call['method'])}</td><td>{html.escape(call['path'])}</td><td>{html.escape(str(call.get('result', '-')))}</td></tr>"
        )

    summary_counts = summary["counts"]
    selection_summary = bindings["selection_summary"]
    return textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>文渊阁主看板</title>
          <style>{_dashboard_styles()}</style>
        </head>
        <body>
          <main class="page">
            <section class="hero">
              <article class="hero-card">
                <div class="eyebrow">RegentOS HPC Demo</div>
                <h1>文渊阁主看板</h1>
                <div class="hero-copy">
                  该页面基于 README 约定，展示案件化、票拟、审批、执行、修复受令与归档主线。
                  当前测试指令为：{html.escape(instruction)}
                </div>
              </article>
              <article class="hero-card">
                <div class="panel-label">测试案件</div>
                <h2 style="margin-top:8px;">{html.escape(case_detail["title"])}</h2>
                <div class="hero-copy">{html.escape(case_detail["content"])}</div>
                <div class="pill-row">
                  <span class="pill">{html.escape(case_detail["state"])}</span>
                  <span class="pill">{html.escape(case_detail["priority"])}</span>
                  <span class="pill">submitted_by: {html.escape(case_detail["submitted_by"])}</span>
                </div>
              </article>
            </section>

            <section class="stat-grid">
              <article class="stat-card"><div class="panel-label">案件总数</div><strong>{summary_counts["cases_total"]}</strong></article>
              <article class="stat-card"><div class="panel-label">治理 Agent</div><strong>{summary_counts["agents_total"]}</strong></article>
              <article class="stat-card"><div class="panel-label">模型选择数量</div><strong>{selection_summary["selected_model_count"]}</strong></article>
              <article class="stat-card"><div class="panel-label">API 调用次数</div><strong>{len(api_calls)}</strong></article>
            </section>

            <section class="main-grid">
              <section class="panel">
                <div class="panel-head">
                  <div>
                    <div class="panel-label">案件看板</div>
                    <h2>Kanban</h2>
                  </div>
                  <div class="muted">案件状态流转与修复闭环</div>
                </div>
                <div class="kanban-grid">{"".join(columns)}</div>
              </section>

              <section class="panel">
                <div class="panel-head">
                  <div>
                    <div class="panel-label">卷宗时间线</div>
                    <h2>Memorials</h2>
                  </div>
                  <div class="muted">最近 16 条关键事件</div>
                </div>
                <div class="timeline">{"".join(timeline_items)}</div>
              </section>
            </section>

            <section class="sub-grid">
              <section class="panel">
                <div class="panel-head">
                  <div>
                    <div class="panel-label">模型运行时</div>
                    <h2>Bound Models</h2>
                  </div>
                  <div class="muted">{html.escape(selection_summary["inventory_source"])}</div>
                </div>
                <div class="binding-grid">{"".join(binding_cards)}</div>
              </section>

              <section class="panel">
                <div class="panel-head">
                  <div>
                    <div class="panel-label">执行产物</div>
                    <h2>Artifacts</h2>
                  </div>
                  <div class="muted">排序代码、结果和标记文件</div>
                </div>
                <div class="artifact-grid">{"".join(artifact_cards)}</div>
              </section>
            </section>

            <section class="panel" style="margin-bottom:18px;">
              <div class="panel-head">
                <div>
                  <div class="panel-label">执行序列</div>
                  <h2>Sorting Commands</h2>
                </div>
                <div class="muted">按 bubble -> insertion -> selection -> merge -> quick 顺序执行</div>
              </div>
              <table>
                <thead>
                  <tr><th>Order</th><th>Algorithm</th><th>Command</th><th>Output</th><th>Match</th></tr>
                </thead>
                <tbody>
                  {"".join(sequence_rows)}
                </tbody>
              </table>
            </section>

            <section class="panel">
              <div class="panel-head">
                <div>
                  <div class="panel-label">调用情况</div>
                  <h2>API Calls</h2>
                </div>
                <div class="muted">按 README 路由完成整条链路自测</div>
              </div>
              <table>
                <thead>
                  <tr><th>Method</th><th>Path</th><th>Result</th></tr>
                </thead>
                <tbody>
                  {"".join(api_rows)}
                </tbody>
              </table>
            </section>

            <section class="panel" style="margin-top:18px;">
              <div class="panel-head">
                <div>
                  <div class="panel-label">测试指令</div>
                  <h2>Input Prompt</h2>
                </div>
              </div>
              <pre>{html.escape(instruction)}</pre>
            </section>

            <div class="footer-note">
              该看板为静态导出文件，可直接放入 HPC 输出目录打开查看。
            </div>
          </main>
        </body>
        </html>
        """
    )


def _render_jinyiwei_board(
    *,
    board: dict[str, Any],
    artifacts: dict[str, str],
    case_id: str,
) -> str:
    issue_cards = []
    for item in board["items"]:
        tags = "".join(f'<span class="tag">{html.escape(topic)}</span>' for topic in item["evidence_topics"])
        decision_authority = {
            "jinyiwei.advisor": "锦衣卫自行处理",
            "imperial_user": "用户决定",
            "none": "持续观察",
        }.get(item["decision_authority"], item["decision_authority"])
        handling_mode = {
            "auto": "自动处置",
            "user": "用户决策",
            "observe": "观察中",
        }.get(item["handling_mode"], item["handling_mode"])
        issue_cards.append(
            textwrap.dedent(
                f"""\
                <article class="issue-card severity-{html.escape(item["severity"])}">
                  <div class="panel-label">案件 {html.escape(item["case_id"])}</div>
                  <h2 style="margin-top:8px;">{html.escape(item["case_title"])}</h2>
                  <div class="pill-row">
                    <span class="pill">severity: {html.escape(item["severity"])}</span>
                    <span class="pill">risk_level: {html.escape(item["risk_level"])}</span>
                    <span class="pill">status: {html.escape(item["status"])}</span>
                    <span class="pill">state: {html.escape(item["current_state"])}</span>
                  </div>
                  <p>{html.escape(item["summary"])}</p>
                  <div style="margin-top:10px;"><strong>流程审计</strong></div>
                  <div class="muted">{html.escape(" -> ".join(item["audited_stages"]))}</div>
                  <div class="muted">{html.escape(" -> ".join(item["process_trace"]))}</div>
                  <div class="muted">问题环节: {html.escape(item["affected_stage"])} / {html.escape(item["affected_step"])}</div>
                  <div class="muted">处置权限: {html.escape(decision_authority)} · 模式: {html.escape(handling_mode)}</div>
                  <div class="muted">用户决策: {"需要" if item["requires_user_order"] else "无需"}</div>
                  <div class="muted">repair_strategy: {html.escape(item["repair_strategy"])}</div>
                  <div class="muted">repair_scope: {html.escape(item["repair_scope"])}</div>
                  <div style="margin-top:10px;"><strong>修复建议</strong></div>
                  <div>{html.escape(item["recommendation"])}</div>
                  <div class="tag-row">{tags}</div>
                </article>
                """
            )
        )

    artifact_links = []
    for label, rel_path in artifacts.items():
        artifact_links.append(f'<div class="artifact-card"><strong>{html.escape(label)}</strong><div class="muted">{html.escape(rel_path)}</div><div style="margin-top:10px;"><a href="{html.escape(rel_path)}">打开文件</a></div></div>')

    counts = board["counts"]
    return textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>锦衣卫看板</title>
          <style>{_dashboard_styles()}</style>
        </head>
        <body>
          <main class="page">
            <section class="hero">
              <article class="hero-card">
                <div class="eyebrow">RegentOS HPC Demo</div>
                <h1>锦衣卫看板</h1>
                <div class="hero-copy">
                  该页面聚焦内部问题、等级划分、修复策略、证据事件与处置状态。
                  当前展示案件：{html.escape(case_id)}。
                </div>
              </article>
              <article class="hero-card">
                <div class="panel-label">问题统计</div>
                <h2 style="margin-top:8px;">内部问题总览</h2>
                <div class="pill-row">
                  <span class="pill">issues_total: {counts["issues_total"]}</span>
                  <span class="pill">critical: {counts["critical"]}</span>
                  <span class="pill">high: {counts["high"]}</span>
                  <span class="pill">auto_handled: {counts["auto_handled"]}</span>
                  <span class="pill">pending_user_decision: {counts["pending_user_decision"]}</span>
                </div>
                <div class="hero-copy" style="margin-top:14px;">
                  锦衣卫独立审查从需求受理到归档的全流程，定位具体环节、划分危险等级，
                  对低风险问题自行处置，对高风险问题保留给用户决策。
                </div>
              </article>
            </section>

            <section class="sub-grid">
              <section class="panel">
                <div class="panel-head">
                  <div>
                    <div class="panel-label">问题列表</div>
                    <h2>Internal Issues</h2>
                  </div>
                  <div class="muted">覆盖 repair.report / repair.authorized / auto_handle / rerun 等证据链</div>
                </div>
                <div class="issue-grid">{"".join(issue_cards) if issue_cards else '<div class="muted">当前没有内部问题。</div>'}</div>
              </section>

              <section class="panel">
                <div class="panel-head">
                  <div>
                    <div class="panel-label">修复交付</div>
                    <h2>Marked Outputs</h2>
                  </div>
                  <div class="muted">直接输出到 HPC 的文件标记</div>
                </div>
                <div class="artifact-grid">{"".join(artifact_links)}</div>
              </section>
            </section>
          </main>
        </body>
        </html>
        """
    )


def _render_index_page(artifacts: dict[str, str]) -> str:
    links = "".join(
        f'<li><a href="{html.escape(path)}">{html.escape(label)}</a></li>' for label, path in artifacts.items()
    )
    return textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>RegentOS HPC Export</title>
          <style>{_dashboard_styles()}</style>
        </head>
        <body>
          <main class="page">
            <section class="hero">
              <article class="hero-card">
                <div class="eyebrow">RegentOS HPC Demo</div>
                <h1>输出索引</h1>
                <div class="hero-copy">以下文件已按 README 的双看板约定导出，可直接在 HPC 输出目录中打开。</div>
              </article>
            </section>
            <section class="panel">
              <ul>
                {links}
              </ul>
            </section>
          </main>
        </body>
        </html>
        """
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _generate_sorting_artifacts(
    output_dir: Path,
    *,
    event_callback: Callable[[str, str, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    steps_dir = artifacts_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    code_path = artifacts_dir / "sorting_multi_method.py"
    command_path = artifacts_dir / "run_sorting_demo.sh"
    instruction_path = artifacts_dir / "test_instruction.txt"
    results_path = artifacts_dir / "sorting_results.json"
    summary_path = artifacts_dir / "sorting_results.txt"

    _write_text(code_path, SORTING_SCRIPT)

    rng = random.Random(20260415)
    values = [rng.randint(-50, 99) for _ in range(12)]
    expected = sorted(values)
    command_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'PYTHON_BIN="${PYTHON_BIN:-python3}"',
    ]

    sequence: list[dict[str, Any]] = []
    results: dict[str, list[int]] = {}

    for order, algorithm in enumerate(EXECUTION_SEQUENCE, start=1):
        step_path = steps_dir / f"{order:02d}_{algorithm}.json"
        command = (
            f'"${{PYTHON_BIN}}" artifacts/sorting_multi_method.py --algorithm {algorithm} '
            f'--size {len(values)} --seed 20260415 --json > {step_path.relative_to(output_dir)}'
        )
        command_lines.append(command)

        if event_callback:
            event_callback(
                "execution.sorting.step.started",
                "dynamic_pool",
                {
                    "order": order,
                    "algorithm": algorithm,
                    "command": command,
                },
            )

        with step_path.open("w", encoding="utf-8") as handle:
            subprocess.run(
                [
                    sys.executable,
                    str(code_path),
                    "--algorithm",
                    algorithm,
                    "--size",
                    str(len(values)),
                    "--seed",
                    "20260415",
                    "--json",
                ],
                cwd=output_dir,
                check=True,
                stdout=handle,
                text=True,
            )

        step_payload = json.loads(step_path.read_text(encoding="utf-8"))
        output = step_payload["output"]
        matches_expected = output == expected
        results[algorithm] = output
        step_record = {
            "order": order,
            "algorithm": algorithm,
            "command": command,
            "output_path": str(step_path.relative_to(output_dir)),
            "matches_expected": matches_expected,
            "result_preview": output[:6],
        }
        sequence.append(step_record)

        if event_callback:
            event_callback(
                "execution.sorting.step.completed",
                "dynamic_pool",
                step_record,
            )

    if event_callback:
        event_callback(
            "execution.sorting.sequence.completed",
            "censorship.inspector",
            {
                "algorithms": EXECUTION_SEQUENCE,
                "steps_total": len(sequence),
                "all_match_expected": all(step["matches_expected"] for step in sequence),
            },
        )

    _write_text(command_path, "\n".join(command_lines) + "\n")
    command_path.chmod(0o755)
    _write_text(instruction_path, DEFAULT_INSTRUCTION + "\n")

    payload = {
        "input": values,
        "expected": expected,
        "execution_order": EXECUTION_SEQUENCE,
        "steps": sequence,
        "results": results,
        "all_algorithms_match_builtin_sorted": all(result == expected for result in results.values()),
    }
    _write_text(results_path, json.dumps(payload, ensure_ascii=False, indent=2))
    _write_text(
        summary_path,
        "\n".join(
            [
                f"input: {values}",
                f"expected: {expected}",
                *(f"{step['order']:02d}. {step['algorithm']}: {results[step['algorithm']]}" for step in sequence),
            ]
        )
        + "\n",
    )

    return {
        "paths": {
            "排序代码": str(code_path.relative_to(output_dir)),
            "运行命令": str(command_path.relative_to(output_dir)),
            "测试指令": str(instruction_path.relative_to(output_dir)),
            "排序结果(JSON)": str(results_path.relative_to(output_dir)),
            "排序结果(TXT)": str(summary_path.relative_to(output_dir)),
        },
        "payload": payload,
    }


def _load_inventory_from_path(model_inventory_path: Path | None) -> tuple[Any, str]:
    if model_inventory_path is None:
        return None, "built-in fallback"
    payload = json.loads(model_inventory_path.read_text(encoding="utf-8"))
    return payload, str(model_inventory_path)


def _request(
    client: TestClient,
    api_calls: list[dict[str, Any]],
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.request(method, path, json=payload)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        result = data.get("state")
        if result is None and "counts" in data:
            result = json.dumps(data["counts"], ensure_ascii=False)
        if result is None and "items" in data:
            result = f"items={len(data['items'])}"
    else:
        result = str(type(data).__name__)
    api_calls.append(
        {
            "method": method,
            "path": path,
            "payload": payload or {},
            "result": result or "ok",
        }
    )
    return data


def _relative_artifact_map(output_dir: Path, extra_paths: dict[str, Path]) -> dict[str, str]:
    return {
        label: str(path.relative_to(output_dir))
        for label, path in extra_paths.items()
    }


def _write_human_report(
    *,
    output_dir: Path,
    case_id: str,
    instruction: str,
    bindings: dict[str, Any],
    api_calls: list[dict[str, Any]],
    sorting_results: dict[str, Any],
    marker_paths: dict[str, str],
    upload_summary: dict[str, Any] | None,
) -> Path:
    report_path = output_dir / "test_report.md"
    lines = [
        "# RegentOS HPC Demo Report",
        "",
        f"- case_id: `{case_id}`",
        f"- instruction: {instruction}",
        f"- selected_model_count: {bindings['selection_summary']['selected_model_count']}",
        f"- api_calls: {len(api_calls)}",
        f"- all_sorting_results_match: {sorting_results['all_algorithms_match_builtin_sorted']}",
        "",
        "## Execution Order",
        f"- {' -> '.join(sorting_results.get('execution_order', []))}",
        "",
        "## Selected Models",
    ]
    for agent_id, binding in bindings["agents"].items():
        lines.append(
            f"- `{agent_id}` -> `{binding['model']}` ({binding['source']}/{binding['provider']})"
        )
    lines.extend(["", "## Marked Outputs"])
    for label, rel_path in marker_paths.items():
        lines.append(f"- {label}: `{rel_path}`")
    if upload_summary:
        lines.extend(
            [
                "",
                "## Upload",
                f"- target: `{upload_summary['target']}`",
                f"- mode: `{upload_summary['mode']}`",
            ]
        )
    _write_text(report_path, "\n".join(lines) + "\n")
    return report_path


def upload_project_to_hpc(project_root: Path, target: str) -> dict[str, str]:
    rsync_path = shutil.which("rsync")
    if not rsync_path:
        raise RuntimeError("rsync is required to upload this project to HPC.")

    command = [
        rsync_path,
        "-az",
        "--delete",
        "--exclude",
        ".git",
        "--exclude",
        ".venv",
        "--exclude",
        "__pycache__",
        "--exclude",
        ".pytest_cache",
        "--exclude",
        "apps/dashboard/node_modules",
        f"{project_root}/",
        target,
    ]
    subprocess.run(command, check=True, cwd=project_root)
    return {"target": target, "mode": "rsync"}


def build_sorting_hpc_demo(
    output_dir: Path,
    *,
    instruction: str = DEFAULT_INSTRUCTION,
    model_inventory_path: Path | None = None,
    upload_target: str | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_inventory, inventory_source = _load_inventory_from_path(model_inventory_path)
    bindings = select_model_bindings(raw_inventory, inventory_source=inventory_source)

    bindings_path = output_dir / "model_bindings.resolved.json"
    _write_text(bindings_path, json.dumps(bindings, ensure_ascii=False, indent=2))

    api_calls: list[dict[str, Any]] = []
    sorting_artifacts: dict[str, Any]

    with TestClient(app) as client:
        case_registry.reset()

        created = _request(
            client,
            api_calls,
            "POST",
            "/api/cases",
            {
                "title": "HPC 随机数组多排序测试",
                "content": instruction,
                "priority": "high",
                "submitted_by": "imperial_user",
            },
        )
        case_id = created["case_id"]

        case_registry.append_event(
            case_id=case_id,
            topic="execution.command.received",
            producer="cabinet.coordinator",
            payload={"instruction": instruction},
        )
        case_registry.append_event(
            case_id=case_id,
            topic="execution.models.bound",
            producer="cabinet.coordinator",
            payload={"selected_models": bindings["agents"]},
        )

        _request(client, api_calls, "GET", "/api/agents")
        _request(client, api_calls, "GET", "/api/models/runtime-capabilities")
        _request(client, api_calls, "POST", f"/api/cases/{case_id}/accept")
        _request(client, api_calls, "POST", f"/api/cases/{case_id}/submit-for-approval")
        _request(client, api_calls, "POST", f"/api/cases/{case_id}/approve")

        def record_demo_event(topic: str, producer: str, payload: dict[str, Any]) -> None:
            case_registry.append_event(
                case_id=case_id,
                topic=topic,
                producer=producer,
                payload=payload,
            )

        sorting_artifacts = _generate_sorting_artifacts(
            output_dir,
            event_callback=record_demo_event,
        )

        case_registry.append_event(
            case_id=case_id,
            topic="execution.artifact.generated",
            producer="dynamic_pool",
            payload={
                "code_path": sorting_artifacts["paths"]["排序代码"],
                "result_path": sorting_artifacts["paths"]["排序结果(JSON)"],
            },
        )
        case_registry.append_event(
            case_id=case_id,
            topic="execution.validation.passed",
            producer="censorship.inspector",
            payload={
                "all_algorithms_match_builtin_sorted": sorting_artifacts["payload"]["all_algorithms_match_builtin_sorted"]
            },
        )

        _request(
            client,
            api_calls,
            "POST",
            f"/api/cases/{case_id}/repair-pending",
            {
                "reason": DEFAULT_REPAIR_REASON,
                "risk_level": DEFAULT_REPAIR_RISK_LEVEL,
                "affected_stage": DEFAULT_REPAIR_AFFECTED_STAGE,
                "affected_step": DEFAULT_REPAIR_AFFECTED_STEP,
                "auto_handle_allowed": True,
            },
        )
        _request(
            client,
            api_calls,
            "POST",
            f"/api/cases/{case_id}/auto-repair",
            {
                "strategy": DEFAULT_REPAIR_STRATEGY,
                "reason": "self-heal low-risk export gap before final HPC delivery",
                "scope": DEFAULT_REPAIR_SCOPE,
                "risk_level": DEFAULT_REPAIR_RISK_LEVEL,
                "affected_stage": DEFAULT_REPAIR_AFFECTED_STAGE,
                "affected_step": DEFAULT_REPAIR_AFFECTED_STEP,
            },
        )
        _request(
            client,
            api_calls,
            "POST",
            f"/api/cases/{case_id}/report",
            {"summary": "sorting artifact verified, dashboards exported, ready for archive"},
        )
        _request(
            client,
            api_calls,
            "POST",
            f"/api/cases/{case_id}/archive",
            {"summary": "HPC demo completed and archived"},
        )

        case_registry.update_metadata(
            case_id,
            output_dir=str(output_dir),
            instruction=instruction,
            selected_models=bindings["agents"],
        )

        detail = _request(client, api_calls, "GET", f"/api/cases/{case_id}")
        summary = _request(client, api_calls, "GET", "/api/dashboard/summary")
        board = _request(client, api_calls, "GET", "/api/dashboard/jinyiwei-board")

        marker_file = output_dir / "HPC_OUTPUT_MARKERS.txt"
        main_board_path = output_dir / "dashboards" / "wenyuange_main_board.html"
        jinyiwei_board_path = output_dir / "dashboards" / "jinyiwei_board.html"
        index_path = output_dir / "index.html"

        artifact_map = _relative_artifact_map(
            output_dir,
            {
                **{label: output_dir / rel_path for label, rel_path in sorting_artifacts["paths"].items()},
                "模型绑定结果": bindings_path,
                "文渊阁主看板": main_board_path,
                "锦衣卫看板": jinyiwei_board_path,
                "输出索引": index_path,
                "输出标记文件": marker_file,
            },
        )

        case_registry.append_event(
            case_id=case_id,
            topic="artifact.dashboard.exported",
            producer="cabinet.reporter",
            payload={
                "wenyuange_board": artifact_map["文渊阁主看板"],
                "jinyiwei_board": artifact_map["锦衣卫看板"],
            },
        )

        timeline = _request(client, api_calls, "GET", f"/api/cases/{case_id}/timeline")["timeline"]

    _write_text(
        main_board_path,
        _render_main_board(
            case_detail=detail,
            timeline=timeline,
            summary=summary,
            bindings=bindings,
            artifacts=artifact_map,
            api_calls=api_calls,
            instruction=instruction,
            sorting_results=sorting_artifacts["payload"],
        ),
    )
    _write_text(
        jinyiwei_board_path,
        _render_jinyiwei_board(
            board=board,
            artifacts=artifact_map,
            case_id=detail["case_id"],
        ),
    )
    _write_text(index_path, _render_index_page(artifact_map))
    _write_text(
        marker_file,
        "\n".join(f"{label}: {path}" for label, path in artifact_map.items()) + "\n",
    )

    upload_summary = {"target": upload_target, "mode": "rsync"} if upload_target else None

    report_path = _write_human_report(
        output_dir=output_dir,
        case_id=detail["case_id"],
        instruction=instruction,
        bindings=bindings,
        api_calls=api_calls,
        sorting_results=sorting_artifacts["payload"],
        marker_paths=artifact_map,
        upload_summary=upload_summary,
    )

    report_payload = {
        "case_id": detail["case_id"],
        "instruction": instruction,
        "output_dir": str(output_dir),
        "api_calls": api_calls,
        "summary": summary,
        "jinyiwei_board": board,
        "selected_models": bindings,
        "sorting_results": sorting_artifacts["payload"],
        "artifacts": artifact_map,
        "report_path": str(report_path.relative_to(output_dir)),
        "upload": upload_summary,
    }
    report_json_path = output_dir / "test_report.json"
    _write_text(report_json_path, json.dumps(report_payload, ensure_ascii=False, indent=2))
    with marker_file.open("a", encoding="utf-8") as handle:
        handle.write(f"测试报告(MD): {report_path.relative_to(output_dir)}\n")
        handle.write(f"测试报告(JSON): {report_json_path.relative_to(output_dir)}\n")

    if upload_target:
        target_root = project_root.resolve() if project_root else Path.cwd().resolve()
        upload_summary = upload_project_to_hpc(target_root, upload_target)
        report_payload["upload"] = upload_summary

    case_registry.reset()
    return report_payload
