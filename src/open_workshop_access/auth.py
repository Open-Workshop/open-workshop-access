from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from open_workshop_access import settings as config


def _token_matches(token: str, stored: str) -> bool:
    if not stored:
        return False
    return token == stored


def _bearer_token(authorization: str) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()


async def require_service_token(
    request: Request,
    authorization: str = Header("", alias="Authorization"),
) -> None:
    _ = request
    if not _token_matches(_bearer_token(authorization), config.ACCESS_SERVICE_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
