from hb_bot.access import is_private_allowed


def test_access_allows_allowlisted_user_in_private_chat():
    assert is_private_allowed(10, "private", frozenset({10}))


def test_access_denies_callback_user_not_in_allowlist():
    assert not is_private_allowed(11, "private", frozenset({10}))


def test_access_denies_groups_even_for_allowlisted_user():
    assert not is_private_allowed(10, "group", frozenset({10}))
    assert not is_private_allowed(10, "supergroup", frozenset({10}))


def test_access_denies_updates_without_user():
    assert not is_private_allowed(None, "private", frozenset({10}))
