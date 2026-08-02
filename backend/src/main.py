"""FastAPI application entrypoint.

API-first: the UI is a client of this same API surface, never a
privileged path (PRD §24, Phase 7 §2's symmetry principle).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.health import router as health_router
from src.api.routers.analysis import router as analysis_router
from src.api.routers.brand_history import router as brand_history_router
from src.api.routers.brands import router as brands_router
from src.api.routers.campaigns import router as campaigns_router
from src.api.routers.explainability import router as explainability_router
from src.api.routers.genomes import router as genomes_router
from src.api.routers.organizations import router as organizations_router
from src.api.routers.policies import router as policies_router
from src.api.routers.reports import router as reports_router
from src.api.routers.session import router as session_router
from src.api.routers.users import router as users_router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(session_router)
app.include_router(organizations_router)
app.include_router(users_router)
app.include_router(brands_router)
app.include_router(campaigns_router)
app.include_router(brand_history_router)
app.include_router(genomes_router)
app.include_router(policies_router)
app.include_router(analysis_router)
app.include_router(explainability_router)
app.include_router(reports_router)

# `docker-compose.yml`'s `prometheus.yml` scrapes `backend:8000/metrics`
# unconditionally (the "observability" profile only gates whether
# Prometheus/Grafana themselves run, not whether this app exposes the
# endpoint) — without this, every scrape 404s. Standard request-count/
# latency/in-progress/exception metrics; no custom business metrics yet.
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("brandium.startup", environment=settings.environment)
