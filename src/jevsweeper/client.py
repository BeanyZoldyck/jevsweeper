from __future__ import annotations

import os

from typesafe_sdk import RetryPolicy, TypeSafeClient

DEFAULT_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_API_KEY = "local"
DEFAULT_TIMEOUT = 300.0


def make_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> TypeSafeClient:
    """HTTP client aimed at a local-jev server (Jev-compatible /v1/systemone)."""
    resolved_model = model or os.environ.get("TYPESAFE_DEFAULT_MODEL") or os.environ.get("LOCAL_JEV_MODEL")
    kwargs: dict = {
        "base_url": (
            base_url
            or os.environ.get("TYPESAFE_BASE_URL")
            or os.environ.get("LOCAL_JEV_URL")
            or DEFAULT_BASE_URL
        ),
        "api_key": api_key or os.environ.get("TYPESAFE_API_KEY") or DEFAULT_API_KEY,
        "timeout": timeout,
        "retry": RetryPolicy(timeout=timeout),
    }
    if resolved_model:
        kwargs["model"] = resolved_model
    return TypeSafeClient(**kwargs)
