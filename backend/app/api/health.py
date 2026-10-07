import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session

router = APIRouter(tags=["health"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(session: SessionDependency, response: Response) -> dict[str, str]:
    try:
        async with asyncio.timeout(get_settings().db_timeout_seconds):
            await session.execute(text("SELECT 1 FROM appointments LIMIT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ready"}
