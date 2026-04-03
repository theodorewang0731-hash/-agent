import json
from pathlib import Path


def ensure_json(path: Path, default: object) -> None:
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    runtime = Path("runtime")
    data = Path("data")
    runtime.mkdir(exist_ok=True)
    data.mkdir(exist_ok=True)

    for slug in [
        "cabinet-coordinator",
        "cabinet-drafter",
        "cabinet-reviewer",
        "cabinet-dispatcher",
        "cabinet-reporter",
        "silijian-approver",
        "silijian-decree_writer",
        "silijian-rejector",
        "censorship-personnel",
        "censorship-finance",
        "censorship-protocol",
        "censorship-military",
        "censorship-justice",
        "censorship-engineering",
        "censorship-inspector",
        "jinyiwei-locator",
        "jinyiwei-analyzer",
        "jinyiwei-advisor",
    ]:
        (runtime / "workspaces" / slug).mkdir(parents=True, exist_ok=True)

    ensure_json(data / "live_status.json", {})
    ensure_json(data / "agent_catalog_snapshot.json", {})
    ensure_json(data / "cases_snapshot.json", [])
    ensure_json(data / "model_runtime_snapshot.json", {})
    print("Runtime directories initialized.")


if __name__ == "__main__":
    main()
