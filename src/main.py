from __future__ import annotations

import datetime
import logging

from fastapi import Depends, FastAPI, HTTPException, Path, Request, status

import responses.body as RespBody
from auth import require_service_token
from client import fetch_manager_context
from schemas import (
    AccessModEntry,
    AccessState,
    ContextRequest,
    ModAddRequest,
    ModRequest,
    ModsRequest,
)

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


def _response_context(context: AccessState) -> AccessState:
    if context.last_password_reset and context.password_change_available_at is None:
        context.password_change_available_at = context.last_password_reset + datetime.timedelta(
            minutes=5
        )
    if context.last_username_reset and context.username_change_available_at is None:
        context.username_change_available_at = context.last_username_reset + datetime.timedelta(
            days=30
        )
    return context


def _is_muted(context: AccessState) -> bool:
    return bool(context.mute_until and context.mute_until > datetime.datetime.now())


def _mod_entry_by_id(context: AccessState, mod_id: int) -> AccessModEntry | None:
    if not context.mods:
        return None
    for mod in context.mods:
        if mod.mod_id == mod_id:
            return mod
    return None


def _crud_response(context: AccessState) -> RespBody.SimpleCrudResponse:
    can_manage = bool(context.admin)
    admin_right = RespBody.BaseRight(
        can_manage,
        "Администратор может выполнять действие" if can_manage else "Требуются права администратора",
        "admin" if can_manage else "forbidden",
    )
    return RespBody.SimpleCrudResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        add=admin_right,
        edit=admin_right,
        delete=admin_right,
    )


@app.post(
    "/context",
    summary="Get current static access context",
    response_model=AccessState,
    response_model_exclude_none=True,
)
async def context(
    request: Request,
    payload: ContextRequest,
    _: None = Depends(require_service_token),
) -> AccessState:
    context = _response_context(
        await fetch_manager_context(request, user_id=payload.user_id)
    )
    return context


@app.put(
    "/mod",
    summary="Get mod add access permissions",
    response_model=RespBody.ModAddResponse,
    response_model_exclude_none=True,
)
async def mod_add(
    request: Request,
    payload: ModAddRequest,
    _: None = Depends(require_service_token),
) -> RespBody.ModAddResponse:
    context = _response_context(await fetch_manager_context(request))
    if not context.authenticated or context.owner_id < 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    can_add = bool(context.admin)
    if not can_add:
        if payload.without_author:
            can_add = False
        elif _is_muted(context):
            can_add = False
        else:
            can_add = bool(context.publish_mods)

    if not can_add:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return RespBody.ModAddResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        add=RespBody.BaseRight(
            can_add,
            "Можно публиковать моды" if can_add else "Публикация модов недоступна",
            "allowed" if can_add else "forbidden",
        ),
    )


@app.post(
    "/mod/{mod_id}",
    summary="Get mod access permissions",
    response_model=RespBody.ModResponse,
    response_model_exclude_none=True,
)
async def mod(
    request: Request,
    payload: ModRequest,
    mod_id: int = Path(..., description="ID мода"),
    _: None = Depends(require_service_token),
) -> RespBody.ModResponse:
    context = _response_context(await fetch_manager_context(request, mod_ids=[mod_id]))
    mod = _mod_entry_by_id(context, mod_id)
    muted = _is_muted(context)
    is_admin = bool(context.admin)

    can_read = False
    can_edit = False
    can_manage_authors = False
    can_delete = False

    if mod is not None:
        if is_admin:
            can_read = True
            can_edit = True
            can_manage_authors = True
            can_delete = True
        else:
            if mod.owner or mod.member:
                can_read = True
            elif mod.public <= 1:
                can_read = True

            if not muted:
                if mod.owner:
                    can_edit = bool(context.change_self_mods)
                elif mod.member:
                    can_edit = False
                elif mod.public > 1:
                    can_edit = False
                else:
                    can_edit = bool(context.change_mods)

                if mod.owner:
                    can_manage_authors = not (
                        payload.author_id is not None
                        and payload.author_id == context.owner_id
                        and payload.mode is False
                    )
                elif mod.member:
                    can_manage_authors = (
                        payload.author_id is not None
                        and payload.author_id == context.owner_id
                        and payload.mode is False
                    )
                else:
                    can_manage_authors = bool(context.change_authorship_mods)

                if mod.owner and context.delete_self_mods:
                    can_delete = True
                else:
                    can_delete = bool(context.delete_mods)

    edit_reason = "Администратор имеет доступ" if is_admin else "Доступ к модификации ограничен"
    if mod is not None and mod.owner:
        edit_reason = "Можно редактировать свой мод"
    elif mod is not None and not mod.owner and not mod.member and mod.public <= 1:
        edit_reason = "Можно редактировать публичный мод"
    elif muted:
        edit_reason = "Вы в муте"

    return RespBody.ModResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        info=RespBody.BaseRight(
            can_read,
            "Мод доступен для просмотра" if can_read else "Мод скрыт",
            "public" if can_read else "hidden",
        ),
        edit=RespBody.ModEditResponse(
            title=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
            description=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
            short_description=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
            screenshots=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
            new_version=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
            authors=RespBody.BaseRight(
                can_manage_authors,
                "Можно управлять авторами"
                if can_manage_authors
                else "Управление авторами недоступно",
                "authors" if can_manage_authors else "forbidden",
            ),
            tags=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
            dependencies=RespBody.BaseRight(can_edit, edit_reason, "edit" if can_edit else "forbidden"),
        ),
        delete=RespBody.BaseRight(
            can_delete,
            "Можно удалить мод" if can_delete else "Удаление недоступно",
            "delete" if can_delete else "forbidden",
        ),
        download=RespBody.BaseRight(
            can_read,
            "Мод можно скачать" if can_read else "Скачивание скрыто",
            "public" if can_read else "hidden",
        ),
    )


@app.post(
    "/mods",
    summary="Get batch mod access permissions",
    response_model=RespBody.ModsResponse,
    response_model_exclude_none=True,
)
async def mods(
    request: Request,
    payload: ModsRequest,
    _: None = Depends(require_service_token),
) -> RespBody.ModsResponse:
    context = _response_context(
        await fetch_manager_context(request, mod_ids=payload.mods_ids)
    )
    ids = list(dict.fromkeys(int(mod_id) for mod_id in payload.mods_ids))
    allowed_ids: list[int] = []

    if bool(context.admin):
        allowed_ids = ids
    else:
        muted = _is_muted(context)
        for mod_id in ids:
            mod = _mod_entry_by_id(context, mod_id)
            if mod is None:
                continue
            if payload.edit and muted:
                continue
            if mod.owner:
                if payload.edit and not context.change_self_mods:
                    continue
                allowed_ids.append(mod_id)
                continue
            if mod.member:
                if payload.edit:
                    continue
                allowed_ids.append(mod_id)
                continue
            if mod.public > 1:
                continue
            if payload.edit and not context.change_mods:
                continue
            allowed_ids.append(mod_id)

    return RespBody.ModsResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        allowed_ids=allowed_ids,
    )


@app.patch(
    "/tags",
    summary="Get tags access permissions",
    response_model=RespBody.SimpleCrudResponse,
    response_model_exclude_none=True,
)
async def tags(
    request: Request,
    _: None = Depends(require_service_token),
) -> RespBody.SimpleCrudResponse:
    context = _response_context(await fetch_manager_context(request))
    return _crud_response(context=context)


@app.patch(
    "/genres",
    summary="Get genres access permissions",
    response_model=RespBody.SimpleCrudResponse,
    response_model_exclude_none=True,
)
async def genres(
    request: Request,
    _: None = Depends(require_service_token),
) -> RespBody.SimpleCrudResponse:
    context = _response_context(await fetch_manager_context(request))
    return _crud_response(context=context)


@app.put(
    "/game",
    summary="Get game add permissions",
    response_model=RespBody.GameAddResponse,
    response_model_exclude_none=True,
)
async def game_add(
    request: Request,
    _: None = Depends(require_service_token),
) -> RespBody.GameAddResponse:
    context = _response_context(await fetch_manager_context(request))
    can_manage = bool(context.admin)
    return RespBody.GameAddResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        add=RespBody.BaseRight(
            can_manage,
            "Администратор может добавлять игры"
            if can_manage
            else "Требуются права администратора",
            "admin" if can_manage else "forbidden",
        ),
    )


@app.post(
    "/game/{game_id}",
    summary="Get game access permissions",
    response_model=RespBody.GameResponse,
    response_model_exclude_none=True,
)
async def game(
    request: Request,
    game_id: int = Path(..., description="ID игры/приложения"),
    _: None = Depends(require_service_token),
) -> RespBody.GameResponse:
    context = _response_context(await fetch_manager_context(request))
    can_manage = bool(context.admin)
    game_right = RespBody.BaseRight(
        can_manage,
        "Администратор может менять игру" if can_manage else "Требуются права администратора",
        "admin" if can_manage else "forbidden",
    )
    return RespBody.GameResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        edit=RespBody.GameEditResponse(
            title=game_right,
            description=game_right,
            short_description=game_right,
            screenshots=game_right,
            tags=game_right,
            genres=game_right,
        ),
        delete=RespBody.BaseRight(
            can_manage,
            "Администратор может удалять игру" if can_manage else "Требуются права администратора",
            "admin" if can_manage else "forbidden",
        ),
    )


@app.post(
    "/profile/{profile_id}",
    summary="Get profile access permissions",
    response_model=RespBody.ProfileResponse,
    response_model_exclude_none=True,
)
async def profile(
    request: Request,
    profile_id: int = Path(..., description="ID профиля"),
    _: None = Depends(require_service_token),
) -> RespBody.ProfileResponse:
    context = _response_context(await fetch_manager_context(request))
    now = datetime.datetime.now()
    is_self = context.owner_id >= 0 and context.owner_id == profile_id
    is_admin = bool(context.admin)
    muted = _is_muted(context)

    if not context.authenticated or context.owner_id < 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return RespBody.ProfileResponse(
        **context.model_dump(
            exclude={
                "mods",
                "write_comments",
                "set_reactions",
                "vote_for_reputation",
            },
            exclude_none=True,
        ),
        info=RespBody.ProfileInfoResponse(
            public=RespBody.BaseRight(True, "Профиль доступен для просмотра", "public"),
            meta=RespBody.BaseRight(
                is_admin or is_self,
                "Это ваш профиль"
                if is_self
                else "Вы администратор"
                if is_admin
                else "Скрытая информация недоступна",
                "self" if is_self else "admin" if is_admin else "forbidden",
            ),
        ),
        edit=RespBody.ProfileEditResponse(
            nickname=RespBody.BaseRight(
                is_admin
                or (
                    is_self
                    and bool(context.change_username)
                    and not muted
                    and not (
                        context.username_change_available_at
                        and context.username_change_available_at > now
                    )
                ),
                "Администратор может менять никнейм"
                if is_admin
                else "Можно менять собственный никнейм"
                if is_self and context.change_username
                else "Изменение никнейма недоступно",
                "admin"
                if is_admin
                else "self"
                if is_self and context.change_username
                else "forbidden",
            ),
            grade=RespBody.BaseRight(
                is_admin,
                "Администратор может менять грейд",
                "admin" if is_admin else "forbidden",
            ),
            description=RespBody.BaseRight(
                is_admin or (is_self and bool(context.change_about) and not muted),
                "Администратор может менять описание"
                if is_admin
                else "Можно менять собственное описание"
                if is_self and context.change_about and not muted
                else "Изменение описания недоступно",
                "admin"
                if is_admin
                else "self"
                if is_self and context.change_about and not muted
                else "forbidden",
            ),
            avatar=RespBody.BaseRight(
                is_admin or (is_self and bool(context.change_avatar) and not muted),
                "Администратор может менять аватар"
                if is_admin
                else "Можно менять собственный аватар"
                if is_self and context.change_avatar and not muted
                else "Изменение аватара недоступно",
                "admin"
                if is_admin
                else "self"
                if is_self and context.change_avatar and not muted
                else "forbidden",
            ),
            mute=RespBody.BaseRight(
                is_admin and not is_self,
                "Администратор может назначать мут",
                "admin" if is_admin and not is_self else "forbidden",
            ),
            rights=RespBody.BaseRight(
                is_admin,
                "Только администратор может менять права",
                "admin" if is_admin else "forbidden",
            ),
        ),
        vote_for_reputation=RespBody.BaseRight(
            bool(context.vote_for_reputation) and not muted,
            "Голосование за репутацию доступно",
            "allowed" if context.vote_for_reputation and not muted else "muted",
        ),
        write_comments=RespBody.BaseRight(
            bool(context.write_comments) and not muted,
            "Комментирование доступно",
            "allowed" if context.write_comments and not muted else "muted",
        ),
        set_reactions=RespBody.BaseRight(
            bool(context.set_reactions) and not muted,
            "Реакции доступны",
            "allowed" if context.set_reactions and not muted else "muted",
        ),
        delete=RespBody.BaseRight(
            is_self,
            "Удалять можно только свой профиль",
            "self" if is_self else "forbidden",
        ),
    )
