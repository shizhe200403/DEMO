def is_user_disabled(user) -> bool:
    return getattr(user, "status", "active") == "disabled"


def sync_user_active_flag(user) -> bool:
    user.is_active = not is_user_disabled(user)
    return user.is_active
