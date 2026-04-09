from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app
from core.registry.cases import case_registry


def run_step(client: TestClient, method: str, path: str, payload: dict | None = None) -> dict:
    response = client.request(method, path, json=payload)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "state" in data:
        print(f"{path:<40} -> {data['state']}")
    else:
        print(f"{path:<40} -> ok")
    return data


def main() -> None:
    with TestClient(app) as client:
        case_registry.reset()

        created = run_step(
            client,
            "POST",
            "/api/cases",
            {
                "title": "完整治理链演示",
                "content": "从创建到审批、修复受令、回奏归档的整条流程验证。",
                "priority": "high",
                "submitted_by": "imperial_user",
            },
        )
        case_id = created["case_id"]

        run_step(client, "POST", f"/api/cases/{case_id}/accept")
        run_step(client, "POST", f"/api/cases/{case_id}/submit-for-approval")
        run_step(client, "POST", f"/api/cases/{case_id}/approve")
        run_step(
            client,
            "POST",
            f"/api/cases/{case_id}/repair-pending",
            {"reason": "simulate dependency corruption"},
        )
        run_step(
            client,
            "POST",
            f"/api/cases/{case_id}/repair-order",
            {
                "strategy": "patch_then_rerun",
                "reason": "authorized by user",
                "scope": "executor_pool/api_builder",
            },
        )
        run_step(
            client,
            "POST",
            f"/api/cases/{case_id}/rerun",
            {"reason": "apply patch and return to execution"},
        )
        run_step(
            client,
            "POST",
            f"/api/cases/{case_id}/report",
            {"summary": "execution finished and entered reporting"},
        )
        archived = run_step(
            client,
            "POST",
            f"/api/cases/{case_id}/archive",
            {"summary": "case completed and archived"},
        )

        timeline = client.get(f"/api/cases/{case_id}/timeline").json()["timeline"]
        print("")
        print(f"Final state: {archived['state']}")
        print(f"Timeline events: {len(timeline)}")
        print("Recent topics:")
        for topic in [event["topic"] for event in timeline[-8:]]:
            print(f"  - {topic}")


if __name__ == "__main__":
    main()
