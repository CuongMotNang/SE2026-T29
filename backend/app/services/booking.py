from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain import AppointmentNotFound, InvalidSlot
from app.models import Appointment, AppointmentStatus
from app.repositories import AppointmentRepository

BOOKING_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
SLOT_MINUTES = 30


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_start_time(starts_at: datetime, now: datetime) -> datetime:
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise InvalidSlot("starts_at must include a UTC offset")

    local_start = starts_at.astimezone(BOOKING_TIMEZONE)
    if local_start.minute not in (0, 30) or local_start.second != 0 or local_start.microsecond != 0:
        raise InvalidSlot("starts_at must be on a 30-minute boundary")

    normalized = local_start.astimezone(UTC)
    if normalized <= now.astimezone(UTC):
        raise InvalidSlot("starts_at must be in the future")
    return normalized


class BookingService:
    def __init__(
        self,
        repository: AppointmentRepository,
        now_provider: Callable[[], datetime] = utc_now,
    ) -> None:
        self.repository = repository
        self.now_provider = now_provider

    async def create(self, customer_name: str, starts_at: datetime) -> Appointment:
        normalized_start = normalize_start_time(starts_at, self.now_provider())
        appointment = await self.repository.create(customer_name, normalized_start)
        await self.repository.commit()
        await self.repository.refresh(appointment)
        return appointment

    async def list(self, limit: int, offset: int) -> tuple[list[Appointment], int]:
        return await self.repository.list(limit, offset)

    async def cancel(self, appointment_id: UUID) -> None:
        appointment = await self.repository.get(appointment_id)
        if appointment is None:
            raise AppointmentNotFound("Appointment was not found")

        if appointment.status == AppointmentStatus.CANCELLED.value:
            return

        appointment.status = AppointmentStatus.CANCELLED.value
        appointment.cancelled_at = self.now_provider().astimezone(UTC)
        await self.repository.commit()

    async def available_slots(self, day: date) -> list[datetime]:
        local_start = datetime.combine(day, time.min, tzinfo=BOOKING_TIMEZONE)
        local_end = local_start + timedelta(days=1)
        utc_start = local_start.astimezone(UTC)
        utc_end = local_end.astimezone(UTC)
        booked_starts = await self.repository.booked_starts_between(utc_start, utc_end)
        now = self.now_provider().astimezone(UTC)

        slots: list[datetime] = []
        cursor = local_start
        while cursor < local_end:
            cursor_utc = cursor.astimezone(UTC)
            if cursor_utc > now and cursor_utc not in booked_starts:
                slots.append(cursor)
            cursor += timedelta(minutes=SLOT_MINUTES)
        return slots
