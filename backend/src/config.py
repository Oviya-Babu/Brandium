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
    ollama_llm_model: str = "qwen3:8b-instruct"
    ollama_embedding_model: str = "bge-m3"

    # Groq — optional secondary provider, narrative generation only (Technology Stack v1.1 §15)
    groq_api_key: str | None = None
    groq_narration_model: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
