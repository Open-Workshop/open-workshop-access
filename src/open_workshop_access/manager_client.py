from __future__ import annotations

import httpx
from fastapi import Request

from open_workshop_access import settings as config
from open_workshop_access.contracts.state import AccessState


class ManagerCallbackError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _session_cookies(request: Request) -> dict[str, str]:
    cookies: dict[str, str] = {}

    access_token = request.cookies.get("accessToken", "")
    if access_token:
        cookies["accessToken"] = access_token

    refresh_token = request.cookies.get("refreshToken", "")
    if refresh_token:
        cookies["refreshToken"] = refresh_token

    return cookies


def _normalize_mod_ids(mod_ids: list[int] | int | None) -> list[int]:
    if mod_ids is None:
        return []
    if isinstance(mod_ids, int):
        return [mod_ids]
    return [int(mod_id) for mod_id in mod_ids]


async def fetch_manager_context(
    request: Request,
    *,
    mod_ids: list[int] | int | None = None,
) -> AccessState:
    body: dict[str, object] | None = None
    normalized_mod_ids = _normalize_mod_ids(mod_ids)
    if normalized_mod_ids:
        body = {"mods_ids": normalized_mod_ids}

    url = config.MANAGER_URL.rstrip("/") + "/access/callback/context"
    headers = {"Authorization": f"Bearer {config.ACCESS_CALLBACK_TOKEN}"}
    timeout = httpx.Timeout(float(config.REQUEST_TIMEOUT_SECONDS))

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            post_kwargs: dict[str, object] = {
                "headers": headers,
                "cookies": _session_cookies(request),
            }
            if body is not None:
                post_kwargs["json"] = body
            response = await client.post(url, **post_kwargs)
    except httpx.TimeoutException as exc:  # pragma: no cover - network timeout
        raise ManagerCallbackError(
            f"Manager callback timed out: {exc}",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        raise ManagerCallbackError(
            f"Manager callback failed: {exc}",
            status_code=502,
        ) from exc

    if response.status_code >= 400:
        raise ManagerCallbackError(
            f"Manager callback rejected request with status {response.status_code}",
            status_code=response.status_code,
        )

    try:
        data = response.json()
    except ValueError as exc:  # pragma: no cover - invalid manager payload
        raise ManagerCallbackError(
            "Manager callback returned invalid JSON",
            status_code=502,
        ) from exc

    return AccessState.model_validate(data)
