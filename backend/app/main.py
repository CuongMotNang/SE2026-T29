from fastapi import FastAPI

from app.api import appointments, health, slots, version


def create_app() -> FastAPI:
    application = FastAPI(
        title="Production Readiness Booking API",
        version="0.1.0",
    )
    application.include_router(health.router)
    application.include_router(version.router)
    application.include_router(slots.router)
    application.include_router(appointments.router)
    return application


app = create_app()
