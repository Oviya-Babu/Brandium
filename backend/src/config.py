"""Application configuration via Pydantic Settings (Technology Stack §16).

Identical mechanism locally (.env, git-ignored) and in the cloud (real
environment variables) — no branching between environments. Secrets
proper (API keys, DB credentials in production) are expected to be
injected as environment variables by the deployment's secrets mechanism
(AWS Secrets Manager in cloud, `.env` locally — Technology Stack §17);
this module never reads a secret from anywhere else.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["local", "ci", "staging", "production"] = "local"
    log_level: str = "INFO"

    # PostgreSQL — primary relational store (Technology Stack §5)
    database_url: str = "postgresql+asyncpg://brandium:brandium@localhost:5432/brandium"
    sql_echo: bool = False

    # Redis — cache + Celery broker (Technology Stack §8/§9)
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant — vector database, collection-per-tenant (Technology Stack v1.1 §6)
    qdrant_url: str = "http://localhost:6333"

    # MinIO / S3-compatible object storage (Technology Stack §7)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "brandium"
    s3_secret_key: str = "brandium-dev-secret"
    s3_bucket_name: str = "brandium-assets"
    s3_region: str = "us-east-1"

    # Ollama — primary self-hosted LLM + embedding runtime (Technology Stack v1.1 §14/§15)
    ollama_base_url: str = "http://localhost:11434"
    # `qwen3:4b`, not `qwen3:8b-instruct` — the latter is not a real
    # Ollama tag (Qwen3's dense models are instruct-capable by default
    # and published under just their size, e.g. `qwen3:4b`/`qwen3:8b`).
    # 4B chosen as the default for latency/resource footprint; bump to
    # `qwen3:8b` via .env if a host has the headroom and wants the
    # larger model's extra capability.
    ollama_llm_model: str = "qwen3:4b"
    ollama_embedding_model: str = "bge-m3"

    # Groq — automatic fallback when Ollama is unavailable or fails
    # (shared_kernel/llm/client.py), not narration-only by convention
    # anymore. Unset (None) disables the fallback entirely — Ollama
    # failures then raise instead of silently trying a nonexistent
    # secondary provider.
    groq_api_key: str | None = None
    groq_narration_model: str | None = None

    # CORS — the Next.js frontend (localhost:3000) and the FastAPI backend
    # (localhost:8000) are different origins even in local dev (PRD §24's
    # API-first symmetry means the browser calls this API directly, not
    # through a same-origin proxy), so the API must explicitly allow it.
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
