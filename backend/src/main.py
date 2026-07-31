"""FastAPI application entrypoint.

API-first: the UI is a client of this same API surface, never a
privileged path (PRD §24). Only the health check is wired up in this
milestone — every future router is added here, never given a separate
undocumented entry into the app.
"""
from __future__ import annotations

from fastapi import FastAPI

from src.api.health import router as health_router
from src.config import get_settings
from src.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

settings = get_settings()

app = FastAPI(
    title="BrandGuard AI",
    description="Enterprise Brand Decision Intelligence Platform — API",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.include_router(health_router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("brandium.startup", environment=settings.environment)
