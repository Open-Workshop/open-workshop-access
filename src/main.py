import logging

from fastapi import FastAPI, Request, Depends
import responses.body as RespBody
from auth import get_auth, JWTPayload, AUTH_ERROR_RESPONSES


logger = logging.getLogger("open_workshop.access")


app = FastAPI(
    title="Open Workshop Access",
    contact={
        "name": "GitHub",
        "url": "https://github.com/Open-Workshop",
    },
    license_info={
        "name": "GPL-3.0 license",
        "identifier": "GPL-3.0",
    },
    docs_url="/",
)


@app.get(
    "/mod",
    summary="Get mod access permissions",
    response_model=RespBody.ModResponse,
    responses=AUTH_ERROR_RESPONSES,
)
async def mod(
    request: Request,
    auth: JWTPayload = Depends(get_auth)
) -> RespBody.ModResponse:
    return RespBody.ModResponse(
        info=True,
        edit=RespBody.ModEditResponse(
            title=True,
            description=True,
            short_description=True,
            screenshots=True,
            new_version=True,
            authors=True,
            tags=True,
            dependencies=True,
        ),
        delete=True,
        download=True,
    )


@app.get(
    "/tags",
    summary="Get tags access permissions",
    response_model=RespBody.SimpleCrudResponse,
    responses=AUTH_ERROR_RESPONSES,
)
async def tags(
    request: Request,
    auth: JWTPayload = Depends(get_auth)
) -> RespBody.SimpleCrudResponse:
    return RespBody.SimpleCrudResponse(
        add=True,
        edit=True,
        delete=True,
    )


@app.get(
    "/genres",
    summary="Get genres access permissions",
    response_model=RespBody.SimpleCrudResponse,
    responses=AUTH_ERROR_RESPONSES,
)
async def genres(
    request: Request,
    auth: JWTPayload = Depends(get_auth)
) -> RespBody.SimpleCrudResponse:
    return RespBody.SimpleCrudResponse(
        add=True,
        edit=True,
        delete=True,
    )


@app.get(
    "/game",
    summary="Get game access permissions",
    response_model=RespBody.GameResponse,
    responses=AUTH_ERROR_RESPONSES,
)
async def game(
    request: Request,
    auth: JWTPayload = Depends(get_auth)
) -> RespBody.GameResponse:
    return RespBody.GameResponse(
        edit=RespBody.GameEditResponse(
            title=True,
            description=True,
            short_description=True,
            screenshots=True,
            tags=True,
            genres=True,
        ),
        delete=True,
    )


@app.get(
    "/profile",
    summary="Get profile access permissions",
    response_model=RespBody.ProfileResponse,
    responses=AUTH_ERROR_RESPONSES,
)
async def profile(
    request: Request,
    auth: JWTPayload = Depends(get_auth)
) -> RespBody.ProfileResponse:
    return RespBody.ProfileResponse(
        info=RespBody.ProfileInfoResponse(
            public=True,
            meta=True,
        ),
        edit=RespBody.ProfileEditResponse(
            nickname=True,
            grade=True,
            description=True,
            avatar=True,
            mute=True,
            rights=True,
        ),
        vote_for_reputation=True,
        delete=True,
    )