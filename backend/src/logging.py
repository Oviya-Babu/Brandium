"""Structured JSON logging via structlog (Technology Stack §18).

Every log line can carry structured context (`organization_id`,
`analysis_run_id`, `work_unit_id`) so a single AnalysisRun's execution is
traceable across the pipeline without regex-parsing free-text lines
(CLAUDE.md §7). Configured once at process start; call `get_logger(__name__)`
everywhere else.
"""
from __future__ import annotations

import logging
import sys

import structlog

from src.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=settings.log_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
