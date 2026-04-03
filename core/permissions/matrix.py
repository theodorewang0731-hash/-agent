ALLOWED_MESSAGES = {
    "imperial_user": {"gateway"},
    "gateway": {"cabinet"},
    "cabinet": {"silijian", "dynamic_pool", "imperial_user"},
    "silijian": {"cabinet", "imperial_user"},
    "censorship": {"jinyiwei", "imperial_user"},
    "jinyiwei": {"imperial_user"},
    "dynamic_pool": {"cabinet"},
}


def can_message(sender: str, receiver: str) -> bool:
    return receiver in ALLOWED_MESSAGES.get(sender, set())
