from core.registry.cases import case_registry
from core.state_machine.guards import assert_valid_transition


class Orchestrator:
    def accept_case(self, case_id: str) -> None:
        case_registry.update_state(case_id, "accepted", producer="gateway")
        case_registry.update_state(case_id, "planning", producer="cabinet.coordinator")
        case_registry.append_event(
            case_id=case_id,
            topic="case.planning.started",
            producer="cabinet.coordinator",
            payload={"message": "Case entered planning stage"},
        )

    def submit_for_approval(self, case_id: str) -> None:
        case_registry.update_state(case_id, "internal_review", producer="cabinet.reviewer")
        case_registry.update_state(
            case_id,
            "submitted_for_approval",
            producer="cabinet.coordinator",
        )

    def approve_case(self, case_id: str) -> None:
        case_registry.update_state(case_id, "approved", producer="silijian.approver")
        case_registry.update_state(case_id, "dispatched", producer="cabinet.dispatcher")
        case_registry.update_state(case_id, "executing", producer="dynamic_pool")

    def reject_case(self, case_id: str, reason: str) -> None:
        case_registry.update_state(case_id, "rejected", producer="silijian.rejector")
        case_registry.append_event(
            case_id=case_id,
            topic="case.approval.rejected",
            producer="silijian.rejector",
            payload={"reason": reason},
        )

    def request_rework(self, case_id: str, reason: str) -> None:
        case_registry.update_state(case_id, "reworking", producer="cabinet.coordinator")
        case_registry.append_event(
            case_id=case_id,
            topic="case.rework.requested",
            producer="cabinet.coordinator",
            payload={"reason": reason},
        )

    def mark_repair_pending(
        self,
        case_id: str,
        reason: str,
        *,
        risk_level: str | None = None,
        affected_stage: str | None = None,
        affected_step: str | None = None,
        auto_handle_allowed: bool | None = None,
    ) -> None:
        case_registry.update_state(case_id, "repair_pending", producer="jinyiwei.locator")
        case_registry.append_event(
            case_id=case_id,
            topic="repair.report.generated",
            producer="jinyiwei.advisor",
            payload={
                "reason": reason,
                "risk_level": risk_level,
                "affected_stage": affected_stage,
                "affected_step": affected_step,
                "auto_handle_allowed": auto_handle_allowed,
            },
        )

    def authorize_repair(
        self,
        case_id: str,
        strategy: str,
        reason: str,
        scope: str | None,
        *,
        producer: str = "imperial_user",
        decision_mode: str | None = None,
        risk_level: str | None = None,
        affected_stage: str | None = None,
        affected_step: str | None = None,
    ) -> None:
        case_registry.update_state(case_id, "repair_authorized", producer=producer)
        case_registry.append_event(
            case_id=case_id,
            topic="repair.authorized",
            producer=producer,
            payload={
                "strategy": strategy,
                "reason": reason,
                "scope": scope,
                "decision_mode": decision_mode,
                "risk_level": risk_level,
                "affected_stage": affected_stage,
                "affected_step": affected_step,
            },
        )

    def auto_handle_repair(
        self,
        case_id: str,
        strategy: str,
        reason: str,
        scope: str | None,
        *,
        risk_level: str = "low",
        affected_stage: str | None = None,
        affected_step: str | None = None,
    ) -> None:
        self.authorize_repair(
            case_id=case_id,
            strategy=strategy,
            reason=reason,
            scope=scope,
            producer="jinyiwei.advisor",
            decision_mode="auto_handle",
            risk_level=risk_level,
            affected_stage=affected_stage,
            affected_step=affected_step,
        )
        case_registry.append_event(
            case_id=case_id,
            topic="repair.auto_handled",
            producer="jinyiwei.advisor",
            payload={
                "strategy": strategy,
                "reason": reason,
                "scope": scope,
                "risk_level": risk_level,
                "affected_stage": affected_stage,
                "affected_step": affected_step,
            },
        )
        self.rerun_case(
            case_id=case_id,
            reason=reason,
            requested_by="jinyiwei.advisor",
        )

    def rerun_case(
        self,
        case_id: str,
        reason: str | None = None,
        *,
        requested_by: str = "imperial_user",
    ) -> None:
        case_registry.update_state(case_id, "rerunning", producer="dynamic_pool")
        case_registry.append_event(
            case_id=case_id,
            topic="repair.rerun.started",
            producer="dynamic_pool",
            payload={"reason": reason or "authorized rerun", "requested_by": requested_by},
        )
        case_registry.update_state(case_id, "executing", producer="dynamic_pool")
        case_registry.append_event(
            case_id=case_id,
            topic="repair.rerun.completed",
            producer="dynamic_pool",
            payload={"result": "case returned to executing", "requested_by": requested_by},
        )

    def mark_reporting(self, case_id: str, summary: str | None = None) -> None:
        case_registry.update_state(case_id, "reporting", producer="cabinet.reporter")
        case_registry.append_event(
            case_id=case_id,
            topic="case.reporting.started",
            producer="cabinet.reporter",
            payload={"summary": summary or "Execution entered reporting stage"},
        )

    def archive_case(self, case_id: str, summary: str | None = None) -> None:
        case_registry.update_state(case_id, "archived", producer="cabinet.reporter")
        case_registry.append_event(
            case_id=case_id,
            topic="case.archived",
            producer="cabinet.reporter",
            payload={"summary": summary or "Case archived"},
        )

    def pause_case(self, case_id: str) -> None:
        case = case_registry.get_case(case_id)
        if not case:
            raise KeyError(case_id)
        if case["state"] == "paused":
            return
        assert_valid_transition(case["state"], "paused")
        case_registry.update_metadata(case_id, last_active_state=case["state"])
        case_registry.update_state(case_id, "paused", producer="imperial_user")

    def resume_case(self, case_id: str) -> None:
        case = case_registry.get_case(case_id)
        if not case:
            raise KeyError(case_id)
        if case["state"] != "paused":
            return
        target_state = case.get("metadata", {}).get("last_active_state", "executing")
        assert_valid_transition(case["state"], target_state)
        case_registry.update_state(case_id, target_state, producer="imperial_user")

    def freeze_case(self, case_id: str) -> None:
        case_registry.update_state(case_id, "frozen", producer="imperial_user")

    def cancel_case(self, case_id: str) -> None:
        case_registry.update_state(case_id, "cancelled", producer="imperial_user")


orchestrator = Orchestrator()
