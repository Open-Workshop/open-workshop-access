from __future__ import annotations

import datetime

from fastapi import Depends, FastAPI, Path, Request

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
        value=can_manage,
        reason=(
            "Администратор может выполнять действие"
            if can_manage
            else "Требуются права администратора"
        ),
        reason_code="admin" if can_manage else "forbidden",
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
    return await fetch_manager_context(request, user_id=payload.user_id)


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
    context = await fetch_manager_context(request)
    muted = _is_muted(context)

    can_add = False
    add_reason = "Требуется авторизация"
    add_reason_code = "unauthorized"

    if context.authenticated and context.owner_id >= 0:
        if context.admin:
            can_add = True
            add_reason = "Администратор может публиковать моды"
            add_reason_code = "admin"
        elif payload.without_author:
            add_reason = "Публикация без автора доступна только администратору"
            add_reason_code = "admin_required"
        elif muted:
            add_reason = "Вы в муте"
            add_reason_code = "muted"
        elif context.publish_mods:
            can_add = True
            add_reason = "Можно публиковать моды"
            add_reason_code = "allowed"
        else:
            add_reason = "Публикация модов недоступна"
            add_reason_code = "forbidden"

    return RespBody.ModAddResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        add=RespBody.BaseRight(
            value=can_add,
            reason=add_reason,
            reason_code=add_reason_code,
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
    context = await fetch_manager_context(request, mod_ids=[mod_id])
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

    edit_right = RespBody.BaseRight(
        value=can_edit,
        reason=edit_reason,
        reason_code="edit" if can_edit else "forbidden",
    )

    return RespBody.ModResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        info=RespBody.BaseRight(
            value=can_read,
            reason="Мод доступен для просмотра" if can_read else "Мод скрыт",
            reason_code="public" if can_read else "hidden",
        ),
        edit=RespBody.ModEditResponse(
            title=edit_right,
            description=edit_right,
            short_description=edit_right,
            screenshots=edit_right,
            new_version=edit_right,
            authors=RespBody.BaseRight(
                value=can_manage_authors,
                reason=(
                    "Можно управлять авторами"
                    if can_manage_authors
                    else "Управление авторами недоступно"
                ),
                reason_code="authors" if can_manage_authors else "forbidden",
            ),
            tags=edit_right,
            dependencies=edit_right,
        ),
        delete=RespBody.BaseRight(
            value=can_delete,
            reason="Можно удалить мод" if can_delete else "Удаление недоступно",
            reason_code="delete" if can_delete else "forbidden",
        ),
        download=RespBody.BaseRight(
            value=can_read,
            reason="Мод можно скачать" if can_read else "Скачивание скрыто",
            reason_code="public" if can_read else "hidden",
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
    context = await fetch_manager_context(
        request,
        user_id=payload.user_id,
        mod_ids=payload.mods_ids,
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
    context = await fetch_manager_context(request)
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
    context = await fetch_manager_context(request)
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
    context = await fetch_manager_context(request)
    can_manage = bool(context.admin)
    return RespBody.GameAddResponse(
        **context.model_dump(exclude={"mods"}, exclude_none=True),
        add=RespBody.BaseRight(
            value=can_manage,
            reason=(
                "Администратор может добавлять игры"
                if can_manage
                else "Требуются права администратора"
            ),
            reason_code="admin" if can_manage else "forbidden",
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
    context = await fetch_manager_context(request)
    can_manage = bool(context.admin)
    game_right = RespBody.BaseRight(
        value=can_manage,
        reason=(
            "Администратор может менять игру"
            if can_manage
            else "Требуются права администратора"
        ),
        reason_code="admin" if can_manage else "forbidden",
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
            value=can_manage,
            reason=(
                "Администратор может удалять игру"
                if can_manage
                else "Требуются права администратора"
            ),
            reason_code="admin" if can_manage else "forbidden",
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
    context = await fetch_manager_context(request)
    now = datetime.datetime.now()
    is_self = context.owner_id >= 0 and context.owner_id == profile_id
    is_admin = bool(context.admin)
    muted = _is_muted(context)
    username_on_cooldown = bool(
        context.username_change_available_at
        and context.username_change_available_at > now
    )

    can_change_nickname = bool(
        is_admin
        or (is_self and context.change_username and not muted and not username_on_cooldown)
    )
    if is_admin:
        nickname_right = RespBody.BaseRight(
            value=True,
            reason="Администратор может менять никнейм",
            reason_code="admin",
        )
    elif is_self and context.change_username and not muted and not username_on_cooldown:
        nickname_right = RespBody.BaseRight(
            value=True,
            reason="Можно менять собственный никнейм",
            reason_code="self",
        )
    elif muted and is_self and context.change_username:
        nickname_right = RespBody.BaseRight(
            value=False,
            reason="Вы в муте",
            reason_code="muted",
        )
    elif username_on_cooldown and is_self and context.change_username:
        nickname_right = RespBody.BaseRight(
            value=False,
            reason="Никнейм пока нельзя менять",
            reason_code="cooldown",
        )
    else:
        nickname_right = RespBody.BaseRight(
            value=False,
            reason="Изменение никнейма недоступно",
            reason_code="forbidden",
        )

    can_change_description = bool(is_admin or (is_self and context.change_about and not muted))
    if is_admin:
        description_right = RespBody.BaseRight(
            value=True,
            reason="Администратор может менять описание",
            reason_code="admin",
        )
    elif is_self and context.change_about and not muted:
        description_right = RespBody.BaseRight(
            value=True,
            reason="Можно менять собственное описание",
            reason_code="self",
        )
    elif muted and is_self and context.change_about:
        description_right = RespBody.BaseRight(
            value=False,
            reason="Вы в муте",
            reason_code="muted",
        )
    else:
        description_right = RespBody.BaseRight(
            value=False,
            reason="Изменение описания недоступно",
            reason_code="forbidden",
        )

    can_change_avatar = bool(is_admin or (is_self and context.change_avatar and not muted))
    if is_admin:
        avatar_right = RespBody.BaseRight(
            value=True,
            reason="Администратор может менять аватар",
            reason_code="admin",
        )
    elif is_self and context.change_avatar and not muted:
        avatar_right = RespBody.BaseRight(
            value=True,
            reason="Можно менять собственный аватар",
            reason_code="self",
        )
    elif muted and is_self and context.change_avatar:
        avatar_right = RespBody.BaseRight(
            value=False,
            reason="Вы в муте",
            reason_code="muted",
        )
    else:
        avatar_right = RespBody.BaseRight(
            value=False,
            reason="Изменение аватара недоступно",
            reason_code="forbidden",
        )

    can_vote_for_reputation = bool(context.vote_for_reputation and not muted)
    vote_right = RespBody.BaseRight(
        value=can_vote_for_reputation,
        reason=(
            "Голосование за репутацию доступно"
            if can_vote_for_reputation
            else "Вы в муте"
            if muted
            else "Голосование за репутацию недоступно"
        ),
        reason_code="allowed" if can_vote_for_reputation else "muted" if muted else "forbidden",
    )
    can_write_comments = bool(context.write_comments and not muted)
    comments_right = RespBody.BaseRight(
        value=can_write_comments,
        reason=(
            "Комментирование доступно"
            if can_write_comments
            else "Вы в муте"
            if muted
            else "Комментирование недоступно"
        ),
        reason_code="allowed" if can_write_comments else "muted" if muted else "forbidden",
    )
    can_set_reactions = bool(context.set_reactions and not muted)
    reactions_right = RespBody.BaseRight(
        value=can_set_reactions,
        reason=(
            "Реакции доступны"
            if can_set_reactions
            else "Вы в муте"
            if muted
            else "Реакции недоступны"
        ),
        reason_code="allowed" if can_set_reactions else "muted" if muted else "forbidden",
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
            public=RespBody.BaseRight(
                value=True,
                reason="Профиль доступен для просмотра",
                reason_code="public",
            ),
            meta=RespBody.BaseRight(
                value=is_admin or is_self,
                reason=(
                    "Это ваш профиль"
                    if is_self
                    else "Вы администратор"
                    if is_admin
                    else "Скрытая информация недоступна"
                ),
                reason_code="self" if is_self else "admin" if is_admin else "forbidden",
            ),
        ),
        edit=RespBody.ProfileEditResponse(
            nickname=nickname_right,
            grade=RespBody.BaseRight(
                value=is_admin,
                reason="Администратор может менять грейд",
                reason_code="admin" if is_admin else "forbidden",
            ),
            description=description_right,
            avatar=avatar_right,
            mute=RespBody.BaseRight(
                value=is_admin and not is_self,
                reason="Администратор может назначать мут",
                reason_code="admin" if is_admin and not is_self else "forbidden",
            ),
            rights=RespBody.BaseRight(
                value=is_admin,
                reason="Только администратор может менять права",
                reason_code="admin" if is_admin else "forbidden",
            ),
        ),
        vote_for_reputation=vote_right,
        write_comments=comments_right,
        set_reactions=reactions_right,
        delete=RespBody.BaseRight(
            value=is_self,
            reason="Удалять можно только свой профиль",
            reason_code="self" if is_self else "forbidden",
        ),
    )
