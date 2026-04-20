from fastapi.testclient import TestClient

from apps.api.main import app
from core.registry.cases import case_registry


def setup_function() -> None:
    case_registry.reset()


def test_api_end_to_end_governance_flow_reaches_archived() -> None:
    with TestClient(app) as client:
        case_registry.reset()

        response = client.post(
            "/api/cases",
            json={
                "title": "端到端流程验证",
                "content": "验证创建、审批、修复受令和归档整条治理链。",
                "priority": "high",
                "submitted_by": "imperial_user",
            },
        )
        assert response.status_code == 200
        case_id = response.json()["case_id"]

        assert client.post(f"/api/cases/{case_id}/accept").json()["state"] == "planning"
        assert (
            client.post(f"/api/cases/{case_id}/submit-for-approval").json()["state"]
            == "submitted_for_approval"
        )
        assert client.post(f"/api/cases/{case_id}/approve").json()["state"] == "executing"
        assert (
            client.post(
                f"/api/cases/{case_id}/repair-pending",
                json={"reason": "simulate dependency corruption"},
            ).json()["state"]
            == "repair_pending"
        )
        assert (
            client.post(
                f"/api/cases/{case_id}/repair-order",
                json={
                    "strategy": "patch_then_rerun",
                    "reason": "authorized by user",
                    "scope": "executor_pool/api_builder",
                },
            ).json()["state"]
            == "repair_authorized"
        )
        assert (
            client.post(
                f"/api/cases/{case_id}/rerun",
                json={"reason": "apply patch and return to execution"},
            ).json()["state"]
            == "executing"
        )
        assert (
            client.post(
                f"/api/cases/{case_id}/report",
                json={"summary": "execution finished and entered reporting"},
            ).json()["state"]
            == "reporting"
        )
        assert (
            client.post(
                f"/api/cases/{case_id}/archive",
                json={"summary": "case completed and archived"},
            ).json()["state"]
            == "archived"
        )

        timeline_response = client.get(f"/api/cases/{case_id}/timeline")
        assert timeline_response.status_code == 200
        topics = [event["topic"] for event in timeline_response.json()["timeline"]]

        assert "case.created" in topics
        assert "case.state.accepted" in topics
        assert "case.state.submitted_for_approval" in topics
        assert "repair.authorized" in topics
        assert "repair.rerun.started" in topics
        assert "case.reporting.started" in topics
        assert "case.archived" in topics


def test_api_auto_repair_flow_returns_to_execution_with_jinyiwei_authority() -> None:
    with TestClient(app) as client:
        case_registry.reset()

        response = client.post(
            "/api/cases",
            json={
                "title": "低风险导出缺口修复",
                "content": "验证锦衣卫可自行处理低风险问题并回到执行态。",
                "priority": "normal",
                "submitted_by": "imperial_user",
            },
        )
        assert response.status_code == 200
        case_id = response.json()["case_id"]

        assert client.post(f"/api/cases/{case_id}/accept").json()["state"] == "planning"
        assert (
            client.post(f"/api/cases/{case_id}/submit-for-approval").json()["state"]
            == "submitted_for_approval"
        )
        assert client.post(f"/api/cases/{case_id}/approve").json()["state"] == "executing"
        assert (
            client.post(
                f"/api/cases/{case_id}/repair-pending",
                json={
                    "reason": "missing dual-dashboard export",
                    "risk_level": "low",
                    "affected_stage": "执行",
                    "affected_step": "dual_dashboard_export",
                    "auto_handle_allowed": True,
                },
            ).json()["state"]
            == "repair_pending"
        )
        assert (
            client.post(
                f"/api/cases/{case_id}/auto-repair",
                json={
                    "strategy": "export_dual_dashboards_then_rerun",
                    "reason": "low-risk output gap",
                    "scope": "runtime/hpc_exports",
                    "risk_level": "low",
                    "affected_stage": "执行",
                    "affected_step": "dual_dashboard_export",
                },
            ).json()["state"]
            == "executing"
        )

        timeline_response = client.get(f"/api/cases/{case_id}/timeline")
        assert timeline_response.status_code == 200
        timeline = timeline_response.json()["timeline"]
        topics = [event["topic"] for event in timeline]

        assert "repair.auto_handled" in topics
        rerun_started = next(event for event in timeline if event["topic"] == "repair.rerun.started")
        assert rerun_started["payload"]["requested_by"] == "jinyiwei.advisor"
