from datetime import time

import pytest
from pydantic import ValidationError

from hb_bot.config import DatabaseSettings, Settings

BASE = {
    "BOT_TOKEN": "123456:TEST_TOKEN_VALUE",
    "DATABASE_URL": "sqlite+aiosqlite:///test.db",
}


def test_settings_parse_lists_time_and_timezone():
    settings = Settings(
        **BASE,
        ALLOWED_USERS="1, 2,2",
        NOTIFY_CHAT_IDS="10,20",
        NOTIFY_TIME="09:30",
        REMINDER_DAYS="7,1,0",
        TIMEZONE="Europe/Moscow",
    )

    assert settings.allowed_users == frozenset({1, 2})
    assert settings.notify_chat_ids == (10, 20)
    assert settings.notify_time == time(9, 30)
    assert settings.reminder_days == (7, 1, 0)
    assert settings.timezone.key == "Europe/Moscow"


def test_settings_accept_legacy_token_name():
    settings = Settings(
        TOKEN=BASE["BOT_TOKEN"],
        DATABASE_URL=BASE["DATABASE_URL"],
        ALLOWED_USERS="42",
    )

    assert settings.bot_token.get_secret_value() == BASE["BOT_TOKEN"]


@pytest.mark.parametrize("value", ["", "1,", "abc", "0", "-3"])
def test_settings_reject_invalid_or_empty_allowlist(value):
    with pytest.raises(ValidationError):
        Settings(**BASE, ALLOWED_USERS=value)


def test_settings_reject_invalid_timezone():
    with pytest.raises(ValidationError):
        Settings(**BASE, ALLOWED_USERS="1", TIMEZONE="Mars/Olympus")


def test_runtime_validation_rejects_notification_recipient_outside_allowlist():
    settings = Settings(**BASE, ALLOWED_USERS="1", NOTIFY_CHAT_IDS="2")

    with pytest.raises(ValueError, match="allowlist"):
        settings.validate_runtime_values()


@pytest.mark.parametrize(
    "database_url",
    ["sqlite:///sync.db", "postgresql://user:pass@host/db", "https://example.org/db"],
)
def test_database_settings_require_supported_async_driver(database_url):
    with pytest.raises(ValidationError):
        DatabaseSettings(DATABASE_URL=database_url)


def test_database_only_settings_do_not_require_telegram_credentials():
    settings = DatabaseSettings(DATABASE_URL="sqlite+aiosqlite:///data.sqlite3")
    assert settings.database_url.endswith("data.sqlite3")


@pytest.mark.parametrize("notify_time", ["1:2", "9:00", "09:0", "24:00"])
def test_settings_require_strict_notification_time(notify_time):
    settings = Settings(**BASE, ALLOWED_USERS="1", NOTIFY_TIME=notify_time)
    with pytest.raises(ValueError, match="HH:MM"):
        settings.validate_runtime_values()


def test_settings_reject_invalid_log_level():
    with pytest.raises(ValidationError):
        Settings(**BASE, ALLOWED_USERS="1", LOG_LEVEL="NOT_A_LEVEL")
