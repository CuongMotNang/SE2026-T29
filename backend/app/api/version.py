from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter(prefix="/api", tags=["version"])


@router.get("/version")
async def version(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    return {"release": settings.release, "commit_sha": settings.commit_sha}
