from __future__ import annotations

from typing import Any

import httpx

from . import settings as config
from .schemas import AccessRequest, AccessState


class ManagerCallbackError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


async def fetch_manager_context(payload: AccessRequest | dict[str, Any]) -> AccessState:
    if isinstance(payload, AccessRequest):
        body = payload.model_dump(exclude_none=True)
    else:
        body = {key: value for key, value in payload.items() if value is not None}

    url = config.MANAGER_URL.rstrip("/") + "/access/callback/context"
    headers = {"x-token": config.ACCESS_CALLBACK_TOKEN}
    timeout = httpx.Timeout(float(config.REQUEST_TIMEOUT_SECONDS))

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body, headers=headers)
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        raise ManagerCallbackError(f"Manager callback failed: {exc}") from exc

    if response.status_code >= 400:
        raise ManagerCallbackError(
            f"Manager callback rejected request with status {response.status_code}",
            status_code=response.status_code,
        )

    try:
        data = response.json()
    except ValueError as exc:  # pragma: no cover - invalid manager payload
        raise ManagerCallbackError("Manager callback returned invalid JSON") from exc

    return AccessState.model_validate(data)
