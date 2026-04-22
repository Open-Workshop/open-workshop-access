from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from . import settings as config


def _token_matches(token: str, stored: str) -> bool:
    if not stored:
        return False
    return token == stored


async def require_service_token(
    request: Request,
    token: str = Header("", alias="x-token"),
) -> None:
    if not _token_matches(token, config.ACCESS_SERVICE_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
