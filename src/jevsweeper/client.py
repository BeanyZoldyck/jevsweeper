from __future__ import annotations

import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from typesafe_sdk import RetryPolicy, TypeSafeClient

HOSTED_BASE_URL = "https://api.typesafe.ai"
LOCAL_BASE_URL = "http://127.0.0.1:8765"
LOCAL_API_KEY = "local"
HOSTED_TIMEOUT = 60.0
LOCAL_TIMEOUT = 300.0


@dataclass(frozen=True)
class ClientTarget:
    backend: str
    base_url: str
    api_key: str
    timeout: float


class BackendConfigError(RuntimeError):
    pass


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _is_local_url(url: str) -> bool:
    lowered = url.lower()
    return any(token in lowered for token in ("127.0.0.1", "localhost", "[::1]", "0.0.0.0"))


def local_jev_up(url: str = LOCAL_BASE_URL, timeout: float = 0.5) -> bool:
    health = url.rstrip("/") + "/healthz"
    try:
        with urllib.request.urlopen(health, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _hosted_api_key(explicit: str | None = None) -> str | None:
    key = explicit or _env("TYPESAFE_API_KEY")
    if key is None or key.lower() in {"local", "none", "changeme"}:
        return None
    return key


def resolve_target(
    *,
    backend: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> ClientTarget:
    """Pick local-jev or hosted TypeSafe from flags, env, or a local health check."""
    requested = (backend or _env("JEV_BACKEND") or "auto").lower()
    if requested not in {"auto", "local", "hosted"}:
        raise BackendConfigError("backend must be auto, local, or hosted")

    url = base_url or _env("TYPESAFE_BASE_URL") or _env("LOCAL_JEV_URL")
    if requested == "auto" and url:
        requested = "local" if _is_local_url(url) else "hosted"

    if requested == "auto":
        if local_jev_up(LOCAL_BASE_URL):
            requested = "local"
        elif _hosted_api_key(api_key):
            requested = "hosted"
        else:
            raise BackendConfigError(
                "No System One backend is configured.\n"
                "Hosted TypeSafe: set TYPESAFE_API_KEY, or pass --backend hosted.\n"
                "local-jev: run `local-jev serve`, or pass --backend local."
            )

    if requested == "local":
        return ClientTarget(
            backend="local",
            base_url=url or LOCAL_BASE_URL,
            api_key=api_key or _env("TYPESAFE_API_KEY") or LOCAL_API_KEY,
            timeout=LOCAL_TIMEOUT,
        )

    hosted_key = _hosted_api_key(api_key)
    if not hosted_key:
        raise BackendConfigError(
            "Hosted TypeSafe needs TYPESAFE_API_KEY. "
            "Or use local-jev with --backend local after `local-jev serve`."
        )
    return ClientTarget(
        backend="hosted",
        base_url=url if url and not _is_local_url(url) else HOSTED_BASE_URL,
        api_key=hosted_key,
        timeout=HOSTED_TIMEOUT,
    )


def make_client(
    *,
    backend: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
) -> TypeSafeClient:
    """HTTP client for local-jev or hosted TypeSafe (same /v1/systemone wire format)."""
    target = resolve_target(backend=backend, base_url=base_url, api_key=api_key)
    resolved_model = model or _env("TYPESAFE_DEFAULT_MODEL") or _env("LOCAL_JEV_MODEL")
    wait = timeout if timeout is not None else target.timeout
    kwargs: dict = {
        "base_url": target.base_url,
        "api_key": target.api_key,
        "timeout": wait,
        "retry": RetryPolicy(timeout=wait),
    }
    if resolved_model:
        kwargs["model"] = resolved_model
    return TypeSafeClient(**kwargs)
