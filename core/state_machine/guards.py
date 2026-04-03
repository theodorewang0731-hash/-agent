from core.state_machine.transitions import VALID_TRANSITIONS


class InvalidTransitionError(ValueError):
    pass


def assert_valid_transition(current_state: str, next_state: str) -> None:
    allowed = VALID_TRANSITIONS.get(current_state, set())
    if next_state not in allowed:
        raise InvalidTransitionError(f"Invalid transition: {current_state} -> {next_state}")
