from copy import deepcopy
from typing import Any
from uuid import uuid4

from core.events.bus import event_bus
from core.events.schemas import Event, utc_now_iso
from core.state_machine.guards import assert_valid_transition


class CaseRegistry:
    def __init__(self) -> None:
        self._cases: dict[str, dict[str, Any]] = {}

    def create_case(
        self,
        title: str,
        content: str,
        priority: str,
        submitted_by: str,
    ) -> dict[str, Any]:
        case_id = str(uuid4())
        now = utc_now_iso()
        case = {
            "case_id": case_id,
            "title": title,
            "content": content,
            "priority": priority,
            "submitted_by": submitted_by,
            "state": "created",
            "rework_count": 0,
            "metadata": {},
            "created_at": now,
            "updated_at": now,
        }
        self._cases[case_id] = case

        event_bus.publish(
            Event(
                case_id=case_id,
                topic="case.created",
                producer="gateway",
                payload={"title": title, "priority": priority},
            )
        )
        return deepcopy(case)

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        case = self._cases.get(case_id)
        return deepcopy(case) if case else None

    def list_cases(self) -> list[dict[str, Any]]:
        cases = sorted(
            self._cases.values(),
            key=lambda case: (case["updated_at"], case["case_id"]),
            reverse=True,
        )
        return [deepcopy(case) for case in cases]

    def update_metadata(self, case_id: str, **updates: Any) -> dict[str, Any]:
        case = self._cases[case_id]
        case.setdefault("metadata", {}).update(updates)
        case["updated_at"] = utc_now_iso()
        return deepcopy(case)

    def update_state(self, case_id: str, next_state: str, producer: str) -> dict[str, Any]:
        case = self._cases[case_id]
        current_state = case["state"]
        assert_valid_transition(current_state, next_state)

        case["state"] = next_state
        case["updated_at"] = utc_now_iso()
        if next_state == "reworking":
            case["rework_count"] += 1

        event_bus.publish(
            Event(
                case_id=case_id,
                topic=f"case.state.{next_state}",
                producer=producer,
                payload={
                    "from": current_state,
                    "to": next_state,
                    "rework_count": case["rework_count"],
                },
            )
        )
        return deepcopy(case)

    def append_event(
        self,
        case_id: str,
        topic: str,
        producer: str,
        payload: dict[str, Any],
    ) -> None:
        if case_id not in self._cases:
            raise KeyError(case_id)
        event_bus.publish(
            Event(
                case_id=case_id,
                topic=topic,
                producer=producer,
                payload=payload,
            )
        )

    def get_timeline(self, case_id: str) -> list[dict[str, Any]]:
        return [event.model_dump() for event in event_bus.get_case_events(case_id)]

    def export_snapshot(self) -> dict[str, Any]:
        return {
            "cases": self.list_cases(),
            "events_by_case": event_bus.all_events(),
        }

    def load_snapshot(self, snapshot: dict[str, Any], replace: bool = True) -> None:
        if replace:
            self.reset()
        for case in snapshot.get("cases", []):
            self._cases[case["case_id"]] = deepcopy(case)
        event_bus.load_events(snapshot.get("events_by_case", {}), replace=False)

    def reset(self) -> None:
        self._cases.clear()
        event_bus.reset()


case_registry = CaseRegistry()
