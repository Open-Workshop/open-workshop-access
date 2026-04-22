import logging

from fastapi import FastAPI, Path, Request
import responses.body as RespBody


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


@app.put(
    "/mod",
    summary="Get mod add access permissions",
    response_model=RespBody.ModAddResponse,
)
async def mod(
    request: Request
) -> RespBody.ModResponse:
    return RespBody.ModAddResponse(
        add=True
    )


@app.post(
    "/mod/{mod_id}",
    summary="Get mod access permissions",
    response_model=RespBody.ModResponse,
)
async def mod(
    request: Request,
    mod_id: int = Path(..., description="ID мода"),
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


@app.patch(
    "/tags",
    summary="Get tags access permissions",
    response_model=RespBody.SimpleCrudResponse,
)
async def tags(
    request: Request
) -> RespBody.SimpleCrudResponse:
    return RespBody.SimpleCrudResponse(
        add=True,
        edit=True,
        delete=True,
    )


@app.patch(
    "/genres",
    summary="Get genres access permissions",
    response_model=RespBody.SimpleCrudResponse,
)
async def genres(
    request: Request
) -> RespBody.SimpleCrudResponse:
    return RespBody.SimpleCrudResponse(
        add=True,
        edit=True,
        delete=True,
    )


@app.put(
    "/game",
    summary="Get game add permissions",
    response_model=RespBody.GameAddResponse,
)
async def game(
    request: Request,
) -> RespBody.GameAddResponse:
    return RespBody.GameAddResponse(
        edit=True
    )

@app.post(
    "/game/{mod_id}",
    summary="Get game access permissions",
    response_model=RespBody.GameResponse,
)
async def game(
    request: Request,
    game_id: int = Path(..., description="ID игры/приложения"),
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


@app.post(
    "/profile/{profile_id}",
    summary="Get profile access permissions",
    response_model=RespBody.ProfileResponse,
)
async def profile(
    request: Request,
    profile_id: int = Path(..., description="ID профиля"),
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