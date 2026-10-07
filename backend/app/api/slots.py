from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.repositories import AppointmentRepository
from app.schemas import SlotRead
from app.services import BookingService

router = APIRouter(prefix="/api/slots", tags=["slots"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[SlotRead])
async def list_available_slots(
    session: SessionDependency,
    day: Annotated[date, Query(alias="date")],
) -> list[SlotRead]:
    service = BookingService(AppointmentRepository(session))
    slots = await service.available_slots(day)
    return [SlotRead(starts_at=starts_at) for starts_at in slots]
