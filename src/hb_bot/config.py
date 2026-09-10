from __future__ import annotations

import re
from datetime import time
from functools import cached_property
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = Field(validation_alias="DATABASE_URL")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            driver = make_url(value).drivername
        except Exception as error:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL") from error
        if driver not in {"sqlite+aiosqlite", "postgresql+asyncpg"}:
            raise ValueError("DATABASE_URL must use sqlite+aiosqlite or postgresql+asyncpg")
        return value


class Settings(DatabaseSettings):
    """Validated application settings loaded from environment variables."""

    bot_token: SecretStr = Field(validation_alias=AliasChoices("BOT_TOKEN", "TOKEN"))
    allowed_users_csv: str = Field(validation_alias="ALLOWED_USERS")
    notify_chat_ids_csv: str = Field(default="", validation_alias="NOTIFY_CHAT_IDS")
    notify_time_raw: str = Field(default="09:00", validation_alias="NOTIFY_TIME")
    reminder_days_csv: str = Field(default="7,1,0", validation_alias="REMINDER_DAYS")
    timezone_name: str = Field(default="Europe/Moscow", validation_alias="TIMEZONE")
    upcoming_days: int = Field(default=7, ge=1, le=366, validation_alias="UPCOMING_DAYS")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @field_validator("allowed_users_csv")
    @classmethod
    def validate_allowed_users(cls, value: str) -> str:
        parts = value.split(",")
        if not parts or any(not part.strip() for part in parts):
            raise ValueError("ALLOWED_USERS must be a comma-separated list of positive IDs")
        try:
            identifiers = [int(part.strip()) for part in parts]
        except ValueError as error:
            raise ValueError("ALLOWED_USERS must contain only integers") from error
        if any(identifier <= 0 for identifier in identifiers):
            raise ValueError("ALLOWED_USERS must contain positive Telegram user IDs")
        return value

    @field_validator("timezone_name")
    @classmethod
    def validate_timezone_name(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Unknown timezone: {value}") from error
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
        return normalized

    @cached_property
    def allowed_users(self) -> frozenset[int]:
        return frozenset(int(part.strip()) for part in self.allowed_users_csv.split(","))

    @cached_property
    def notify_chat_ids(self) -> tuple[int, ...]:
        if not self.notify_chat_ids_csv.strip():
            return ()
        try:
            values = tuple(
                dict.fromkeys(int(part.strip()) for part in self.notify_chat_ids_csv.split(","))
            )
        except ValueError as error:
            raise ValueError("NOTIFY_CHAT_IDS must contain only integers") from error
        if any(value <= 0 for value in values):
            raise ValueError("NOTIFY_CHAT_IDS must contain private chat IDs")
        return values

    @cached_property
    def notify_time(self) -> time:
        if not re.fullmatch(r"\d{2}:\d{2}", self.notify_time_raw):
            raise ValueError("NOTIFY_TIME must use HH:MM format")
        try:
            hour, minute = (int(part) for part in self.notify_time_raw.split(":"))
            return time(hour=hour, minute=minute)
        except (TypeError, ValueError) as error:
            raise ValueError("NOTIFY_TIME must use HH:MM format") from error

    @cached_property
    def reminder_days(self) -> tuple[int, ...]:
        try:
            values = tuple(
                dict.fromkeys(int(part.strip()) for part in self.reminder_days_csv.split(","))
            )
        except ValueError as error:
            raise ValueError("REMINDER_DAYS must contain integers") from error
        if not values or any(value < 0 or value > 366 for value in values):
            raise ValueError("REMINDER_DAYS values must be between 0 and 366")
        return values

    @cached_property
    def timezone(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.timezone_name)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Unknown timezone: {self.timezone_name}") from error

    def validate_runtime_values(self) -> None:
        """Force validation of lazily parsed composite settings at startup."""

        _ = (self.notify_time, self.reminder_days, self.timezone)
        recipients = set(self.notify_chat_ids)
        if not recipients.issubset(self.allowed_users):
            raise ValueError("NOTIFY_CHAT_IDS must be a subset of the ALLOWED_USERS allowlist")
