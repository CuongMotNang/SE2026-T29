from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domain import AppointmentNotFound, InvalidSlot, SlotAlreadyBooked
from app.repositories import AppointmentRepository
from app.schemas import AppointmentCreate, AppointmentList, AppointmentRead
from app.services import BookingService

router = APIRouter(prefix="/api/appointments", tags=["appointments"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


def booking_service(session: AsyncSession) -> BookingService:
    return BookingService(AppointmentRepository(session))


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    session: SessionDependency,
) -> AppointmentRead:
    try:
        appointment = await booking_service(session).create(
            payload.customer_name,
            payload.starts_at,
        )
    except InvalidSlot as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SlotAlreadyBooked as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AppointmentRead.model_validate(appointment)


@router.get("", response_model=AppointmentList)
async def list_appointments(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AppointmentList:
    appointments, total = await booking_service(session).list(limit, offset)
    return AppointmentList(
        items=[AppointmentRead.model_validate(item) for item in appointments],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: UUID,
    session: SessionDependency,
) -> Response:
    try:
        await booking_service(session).cancel(appointment_id)
    except AppointmentNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
