"""Optional LangSmith tracing helpers."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.config import settings

F = TypeVar("F", bound=Callable[..., Any])


def _configure_langsmith_env() -> None:
    if settings.LANGSMITH_API_KEY:
        os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)
    if settings.LANGSMITH_TRACING:
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")


def traceable(name: str, run_type: str = "chain") -> Callable[[F], F]:
    """Return a LangSmith traceable decorator when configured, otherwise no-op."""
    if not settings.LANGSMITH_TRACING or not settings.LANGSMITH_API_KEY:
        return lambda fn: fn

    try:
        _configure_langsmith_env()
        from langsmith import traceable as langsmith_traceable
    except Exception:
        return lambda fn: fn

    return langsmith_traceable(name=name, run_type=run_type)
