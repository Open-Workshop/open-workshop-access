from __future__ import annotations

from fastapi import APIRouter, Path, Request

from open_workshop_access import manager_client
from open_workshop_access.contracts.responses import (
    BaseRight,
    GameAddResponse,
    GameEditResponse,
    GameResponse,
    SimpleCrudResponse,
)
from open_workshop_access.contracts.state import AccessState


router = APIRouter()


def _crud_response(context: AccessState) -> SimpleCrudResponse:
    public_context = context.to_public_context()
    can_manage = bool(context.admin)
    admin_right = BaseRight(
        value=can_manage,
        reason=(
            "Администратор может выполнять действие"
            if can_manage
            else "Требуются права администратора"
        ),
        reason_code="admin" if can_manage else "forbidden",
    )
    return SimpleCrudResponse(
        **public_context.model_dump(exclude_none=True),
        add=admin_right,
        edit=admin_right,
        delete=admin_right,
    )


@router.patch(
    "/tags",
    summary="Get tags access permissions",
    response_model=SimpleCrudResponse,
    response_model_exclude_none=True,
)
async def tags(request: Request) -> SimpleCrudResponse:
    context = await manager_client.fetch_manager_context(request)
    return _crud_response(context)


@router.patch(
    "/genres",
    summary="Get genres access permissions",
    response_model=SimpleCrudResponse,
    response_model_exclude_none=True,
)
async def genres(request: Request) -> SimpleCrudResponse:
    context = await manager_client.fetch_manager_context(request)
    return _crud_response(context)


@router.put(
    "/game",
    summary="Get game add permissions",
    response_model=GameAddResponse,
    response_model_exclude_none=True,
)
async def game_add(request: Request) -> GameAddResponse:
    context = await manager_client.fetch_manager_context(request)
    public_context = context.to_public_context()
    can_manage = bool(context.admin)
    return GameAddResponse(
        **public_context.model_dump(exclude_none=True),
        add=BaseRight(
            value=can_manage,
            reason=(
                "Администратор может добавлять игры"
                if can_manage
                else "Требуются права администратора"
            ),
            reason_code="admin" if can_manage else "forbidden",
        ),
    )


@router.post(
    "/game/{game_id}",
    summary="Get game access permissions",
    response_model=GameResponse,
    response_model_exclude_none=True,
)
async def game(
    request: Request,
    game_id: int = Path(..., description="ID игры/приложения"),
) -> GameResponse:
    _ = game_id
    context = await manager_client.fetch_manager_context(request)
    public_context = context.to_public_context()
    can_manage = bool(context.admin)
    game_right = BaseRight(
        value=can_manage,
        reason=(
            "Администратор может менять игру"
            if can_manage
            else "Требуются права администратора"
        ),
        reason_code="admin" if can_manage else "forbidden",
    )
    return GameResponse(
        **public_context.model_dump(exclude_none=True),
        edit=GameEditResponse(
            title=game_right,
            description=game_right,
            short_description=game_right,
            screenshots=game_right,
            tags=game_right,
            genres=game_right,
        ),
        delete=BaseRight(
            value=can_manage,
            reason=(
                "Администратор может удалять игру"
                if can_manage
                else "Требуются права администратора"
            ),
            reason_code="admin" if can_manage else "forbidden",
        ),
    )
