from __future__ import annotations

import asyncio
from dataclasses import dataclass
from threading import Lock
from time import monotonic

import httpx
from fastapi import Request

from open_workshop_access import settings as config
from open_workshop_access.contracts.state import AccessState


_ManagerContextCacheKey = tuple[str, str, tuple[int, ...], tuple[int, ...]]
_ManagerContextInflightKey = tuple[int, _ManagerContextCacheKey]


@dataclass(frozen=True)
class _CachedManagerContext:
    value: AccessState
    expires_at: float


_manager_context_cache: dict[_ManagerContextCacheKey, _CachedManagerContext] = {}
_manager_context_inflight: dict[
    _ManagerContextInflightKey,
    asyncio.Task[AccessState],
] = {}
_manager_context_cache_lock = Lock()
_manager_context_next_prune_at = 0.0


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


def _manager_context_cache_key(
    request: Request,
    *,
    normalized_mod_ids: list[int],
    normalized_modpack_ids: list[int],
) -> _ManagerContextCacheKey:
    return (
        request.cookies.get("accessToken", ""),
        request.cookies.get("refreshToken", ""),
        tuple(normalized_mod_ids),
        tuple(normalized_modpack_ids),
    )


def _prune_expired_manager_contexts(now: float) -> None:
    global _manager_context_next_prune_at

    if now < _manager_context_next_prune_at:
        return

    for key, cached in list(_manager_context_cache.items()):
        if cached.expires_at <= now:
            del _manager_context_cache[key]
    _manager_context_next_prune_at = now + 1.0


def _clear_manager_context_cache() -> None:
    global _manager_context_next_prune_at

    with _manager_context_cache_lock:
        _manager_context_cache.clear()
        _manager_context_inflight.clear()
        _manager_context_next_prune_at = 0.0


def _remember_manager_context_result(
    task: asyncio.Task[AccessState],
    *,
    cache_key: _ManagerContextCacheKey,
    inflight_key: _ManagerContextInflightKey,
    ttl: float,
) -> None:
    with _manager_context_cache_lock:
        if _manager_context_inflight.get(inflight_key) is task:
            del _manager_context_inflight[inflight_key]

        if task.cancelled() or task.exception() is not None:
            return

        now = monotonic()
        _prune_expired_manager_contexts(now)
        _manager_context_cache[cache_key] = _CachedManagerContext(
            value=task.result(),
            expires_at=now + ttl,
        )


async def _request_manager_context(
    request: Request,
    *,
    normalized_mod_ids: list[int],
    normalized_modpack_ids: list[int],
) -> AccessState:
    body: dict[str, object] | None = None
    if normalized_mod_ids or normalized_modpack_ids:
        body = {}
        if normalized_mod_ids:
            body["mods_ids"] = normalized_mod_ids
        if normalized_modpack_ids:
            body["modpacks_ids"] = normalized_modpack_ids

    url = config.MANAGER_URL.rstrip("/") + "/internal/access/context"
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


async def fetch_manager_context(
    request: Request,
    *,
    mod_ids: list[int] | int | None = None,
    modpack_ids: list[int] | int | None = None,
) -> AccessState:
    normalized_mod_ids = _normalize_mod_ids(mod_ids)
    normalized_modpack_ids = _normalize_mod_ids(modpack_ids)
    ttl = float(config.MANAGER_CONTEXT_CACHE_TTL_SECONDS)
    if ttl <= 0:
        return await _request_manager_context(
            request,
            normalized_mod_ids=normalized_mod_ids,
            normalized_modpack_ids=normalized_modpack_ids,
        )

    cache_key = _manager_context_cache_key(
        request,
        normalized_mod_ids=normalized_mod_ids,
        normalized_modpack_ids=normalized_modpack_ids,
    )
    loop_id = id(asyncio.get_running_loop())
    inflight_key = (loop_id, cache_key)

    with _manager_context_cache_lock:
        now = monotonic()
        _prune_expired_manager_contexts(now)
        cached = _manager_context_cache.get(cache_key)
        if cached is not None and cached.expires_at > now:
            return cached.value
        if cached is not None:
            del _manager_context_cache[cache_key]

        task = _manager_context_inflight.get(inflight_key)
        if task is None:
            task = asyncio.create_task(
                _request_manager_context(
                    request,
                    normalized_mod_ids=normalized_mod_ids,
                    normalized_modpack_ids=normalized_modpack_ids,
                )
            )
            _manager_context_inflight[inflight_key] = task
            task.add_done_callback(
                lambda completed_task: _remember_manager_context_result(
                    completed_task,
                    cache_key=cache_key,
                    inflight_key=inflight_key,
                    ttl=ttl,
                )
            )

    return await asyncio.shield(task)
