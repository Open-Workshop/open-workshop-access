import time
from typing import Annotated, TypedDict

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import responses.status as StatusModel


SECRET_KEY = "CHANGE_ME"
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


class JWTPayload(TypedDict):
    user_id: int
    created_at: int
    refresh_at: int
    exp: int


class AuthContext(BaseModel):
    is_anonymous: bool
    user_id: int | None = None
    created_at: int | None = None
    refresh_at: int | None = None
    exp: int | None = None
    should_refresh: bool = False



AUTH_ERROR_RESPONSES = {
    400: StatusModel.AuthPoorAttempt.openapi(),
    401: StatusModel.AuthExpiredSession.openapi(),
    406: StatusModel.AuthTokenPayloadInvalid.openapi(),
}


def decode_jwt(token: str) -> JWTPayload:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require": ["user_id", "created_at", "refresh_at", "exp"],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise StatusModel.AuthExpiredSession() from exc
    except jwt.MissingRequiredClaimError as exc:
        raise StatusModel.AuthPoorAttempt(
            message=f"Authorization token is missing required claim: {exc.claim}",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise StatusModel.AuthPoorAttempt(
            message="Authorization token is invalid",
        ) from exc

    try:
        normalized: JWTPayload = {
            "user_id": int(payload["user_id"]),
            "created_at": int(payload["created_at"]),
            "refresh_at": int(payload["refresh_at"]),
            "exp": int(payload["exp"]),
        }
    except (TypeError, ValueError, KeyError) as exc:
        raise StatusModel.AuthTokenPayloadInvalid() from exc

    if normalized["created_at"] > normalized["refresh_at"]:
        raise StatusModel.AuthTokenPayloadInvalid(
            message="Authorization token payload is inconsistent: created_at > refresh_at",
        )

    if normalized["refresh_at"] > normalized["exp"]:
        raise StatusModel.AuthTokenPayloadInvalid(
            message="Authorization token payload is inconsistent: refresh_at > exp",
        )

    return normalized


async def get_auth_context(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthContext:
    if credentials is None:
        return AuthContext(is_anonymous=True)

    if credentials.scheme.lower() != "bearer":
        raise StatusModel.AuthPoorAttempt(
            message="Authorization scheme must be Bearer",
        )

    payload = decode_jwt(credentials.credentials)

    now = int(time.time())

    return AuthContext(
        is_anonymous=False,
        user_id=payload["user_id"],
        created_at=payload["created_at"],
        refresh_at=payload["refresh_at"],
        exp=payload["exp"],
        should_refresh=now >= payload["refresh_at"],
    )
