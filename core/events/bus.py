from collections import defaultdict

from core.events.schemas import Event


class InMemoryEventBus:
    def __init__(self) -> None:
        self._events_by_case: dict[str, list[Event]] = defaultdict(list)

    def publish(self, event: Event) -> Event:
        self._events_by_case[event.case_id].append(event)
        return event

    def get_case_events(self, case_id: str) -> list[Event]:
        return list(self._events_by_case.get(case_id, []))

    def all_events(self) -> dict[str, list[dict]]:
        return {
            case_id: [event.model_dump() for event in events]
            for case_id, events in self._events_by_case.items()
        }

    def load_events(self, snapshot: dict[str, list[dict]], replace: bool = False) -> None:
        if replace:
            self.reset()
        for case_id, events in snapshot.items():
            self._events_by_case[case_id] = [Event(**event) for event in events]

    def reset(self) -> None:
        self._events_by_case.clear()


event_bus = InMemoryEventBus()
