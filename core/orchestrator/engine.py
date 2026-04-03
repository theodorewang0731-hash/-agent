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

    def mark_repair_pending(self, case_id: str, reason: str) -> None:
        case_registry.update_state(case_id, "repair_pending", producer="jinyiwei.locator")
        case_registry.append_event(
            case_id=case_id,
            topic="repair.report.generated",
            producer="jinyiwei.advisor",
            payload={"reason": reason},
        )

    def authorize_repair(
        self,
        case_id: str,
        strategy: str,
        reason: str,
        scope: str | None,
    ) -> None:
        case_registry.update_state(case_id, "repair_authorized", producer="imperial_user")
        case_registry.append_event(
            case_id=case_id,
            topic="repair.authorized",
            producer="imperial_user",
            payload={"strategy": strategy, "reason": reason, "scope": scope},
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
