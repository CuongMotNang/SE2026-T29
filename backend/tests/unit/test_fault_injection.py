from datetime import UTC, datetime, timedelta

import pytest

from app.config import Settings
from app.services.fault_injection import BookingFaultInjector, InjectedBookingFault

NOW = datetime(2026, 10, 21, 3, 0, tzinfo=UTC)
FUTURE = NOW + timedelta(hours=1)


def test_settings_load_fault_controls_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("BOOKING_FAULT_MODE", "latency")
    monkeypatch.setenv("BOOKING_FAULT_RATE", "0.25")
    monkeypatch.setenv("BOOKING_FAULT_UNTIL", "2026-10-21T15:00:00+07:00")
    monkeypatch.setenv("BOOKING_FAULT_LATENCY_SECONDS", "1.5")

    settings = Settings(_env_file=None)

    assert settings.fault_mode == "latency"
    assert settings.fault_rate == 0.25
    assert settings.fault_until == datetime.fromisoformat("2026-10-21T15:00:00+07:00")
    assert settings.fault_latency_seconds == 1.5


def test_settings_require_expiry_when_fault_is_active(monkeypatch) -> None:
    monkeypatch.setenv("BOOKING_FAULT_MODE", "error")
    monkeypatch.delenv("BOOKING_FAULT_UNTIL", raising=False)

    with pytest.raises(ValueError, match="BOOKING_FAULT_UNTIL is required"):
        Settings(_env_file=None)


async def test_error_mode_raises_when_selected() -> None:
    injector = BookingFaultInjector(
        mode="error",
        rate=1.0,
        until=FUTURE,
        now_provider=lambda: NOW,
        random_provider=lambda: 0.0,
    )

    with pytest.raises(InjectedBookingFault, match="Injected booking failure"):
        await injector.before_create()


async def test_off_mode_never_injects() -> None:
    injector = BookingFaultInjector(
        mode="off",
        rate=1.0,
        now_provider=lambda: NOW,
        random_provider=lambda: 0.0,
    )

    await injector.before_create()


async def test_rate_can_skip_fault() -> None:
    injector = BookingFaultInjector(
        mode="error",
        rate=0.25,
        until=FUTURE,
        now_provider=lambda: NOW,
        random_provider=lambda: 0.25,
    )

    await injector.before_create()


async def test_fault_automatically_stops_at_until() -> None:
    injector = BookingFaultInjector(
        mode="error",
        rate=1.0,
        until=NOW,
        now_provider=lambda: NOW,
        random_provider=lambda: 0.0,
    )

    await injector.before_create()


async def test_latency_mode_uses_configured_duration() -> None:
    delays: list[float] = []

    async def record_sleep(seconds: float) -> None:
        delays.append(seconds)

    injector = BookingFaultInjector(
        mode="latency",
        rate=1.0,
        until=FUTURE,
        latency_seconds=2.5,
        now_provider=lambda: NOW,
        random_provider=lambda: 0.0,
        sleep=record_sleep,
    )

    await injector.before_create()

    assert delays == [2.5]


def test_active_fault_requires_expiry_even_when_constructed_directly() -> None:
    with pytest.raises(ValueError, match="bounded expiry"):
        BookingFaultInjector(mode="error")
