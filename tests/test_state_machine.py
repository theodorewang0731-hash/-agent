import pytest

from core.state_machine.guards import InvalidTransitionError, assert_valid_transition


def test_valid_transition() -> None:
    assert_valid_transition("created", "accepted")
    assert_valid_transition("approved", "dispatched")


def test_invalid_transition() -> None:
    with pytest.raises(InvalidTransitionError):
        assert_valid_transition("created", "approved")


def test_repair_requires_authorization() -> None:
    with pytest.raises(InvalidTransitionError):
        assert_valid_transition("repair_pending", "rerunning")
