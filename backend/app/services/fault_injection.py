from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal

from app.config import Settings

FaultMode = Literal["off", "error", "latency"]


class InjectedBookingFault(RuntimeError):
    """Expected error used to exercise release and reliability controls."""


class BookingFaultInjector:
    """Apply opt-in, time-bounded faults before a booking is written."""

    def __init__(
        self,
        *,
        mode: FaultMode = "off",
        rate: float = 1.0,
        until: datetime | None = None,
        latency_seconds: float = 3.0,
        now_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
        random_provider: Callable[[], float] = random.random,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if mode not in ("off", "error", "latency"):
            raise ValueError(f"Unsupported fault mode: {mode}")
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Fault rate must be between 0.0 and 1.0")
        if latency_seconds < 0.0:
            raise ValueError("Fault latency must not be negative")
        if mode != "off" and until is None:
            raise ValueError("Active fault mode requires a bounded expiry")
        if until is not None and (until.tzinfo is None or until.utcoffset() is None):
            raise ValueError("Fault expiry must include a UTC offset")

        self.mode = mode
        self.rate = rate
        self.until = until
        self.latency_seconds = latency_seconds
        self.now_provider = now_provider
        self.random_provider = random_provider
        self.sleep = sleep

    @classmethod
    def from_settings(cls, settings: Settings) -> BookingFaultInjector:
        return cls(
            mode=settings.fault_mode,
            rate=settings.fault_rate,
            until=settings.fault_until,
            latency_seconds=settings.fault_latency_seconds,
        )

    async def before_create(self) -> None:
        if not self._should_inject():
            return

        if self.mode == "error":
            raise InjectedBookingFault("Injected booking failure")

        if self.mode == "latency":
            await self.sleep(self.latency_seconds)

    def _should_inject(self) -> bool:
        if self.mode == "off" or self.rate == 0:
            return False

        if self.until is not None:
            now = self.now_provider()
            if now.tzinfo is None or now.utcoffset() is None:
                raise ValueError("now_provider must return a timezone-aware datetime")
            if now.astimezone(UTC) >= self.until.astimezone(UTC):
                return False

        return self.random_provider() < self.rate
