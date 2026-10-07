from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api", tags=["version"])


@router.get("/version")
async def version() -> dict[str, str]:
    settings = get_settings()
    return {"release": settings.release, "commit_sha": settings.commit_sha}
