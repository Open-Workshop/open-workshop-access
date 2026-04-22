from __future__ import annotations

import datetime

from fastapi import APIRouter, Path, Request

from open_workshop_access import manager_client
from open_workshop_access.contracts.requests import ModRequest, ModsRequest
from open_workshop_access.contracts.responses import (
    BaseRight,
    ModAddResponse,
    ModEditResponse,
    ModResponse,
)
from open_workshop_access.contracts.state import AccessModEntry, AccessState


router = APIRouter()


def _is_muted(context: AccessState) -> bool:
    return bool(context.mute_until and context.mute_until > datetime.datetime.now())


def _mod_entry_by_id(context: AccessState, mod_id: int) -> AccessModEntry | None:
    if not context.mods:
        return None
    for mod in context.mods:
        if mod.mod_id == mod_id:
            return mod
    return None


def _mod_response(
    context: AccessState,
    mod_id: int,
    payload: ModRequest | None = None,
) -> ModResponse:
    public_context = context.to_public_context()
    mod_entry = _mod_entry_by_id(context, mod_id)
    muted = _is_muted(context)
    is_admin = bool(context.admin)

    can_read = False
    can_edit = False
    can_manage_authors = False
    can_delete = False

    if mod_entry is not None:
        if is_admin:
            can_read = True
            can_edit = True
            can_manage_authors = True
            can_delete = True
        else:
            if mod_entry.owner or mod_entry.member or mod_entry.public <= 1:
                can_read = True

            if not muted:
                if mod_entry.owner:
                    can_edit = bool(context.change_self_mods)
                elif mod_entry.member or mod_entry.public > 1:
                    can_edit = False
                else:
                    can_edit = bool(context.change_mods)

                if payload is not None:
                    if mod_entry.owner:
                        can_manage_authors = not (
                            payload.author_id is not None
                            and payload.author_id == context.owner_id
                            and payload.mode is False
                        )
                    elif mod_entry.member:
                        can_manage_authors = (
                            payload.author_id is not None
                            and payload.author_id == context.owner_id
                            and payload.mode is False
                        )
                    else:
                        can_manage_authors = bool(context.change_authorship_mods)
                else:
                    can_manage_authors = bool(context.change_authorship_mods)

                if mod_entry.owner and context.delete_self_mods:
                    can_delete = True
                else:
                    can_delete = bool(context.delete_mods)

    edit_reason = "Администратор имеет доступ" if is_admin else "Доступ к модификации ограничен"
    if mod_entry is not None and mod_entry.owner:
        edit_reason = "Можно редактировать свой мод"
    elif mod_entry is not None and not mod_entry.owner and not mod_entry.member and mod_entry.public <= 1:
        edit_reason = "Можно редактировать публичный мод"
    elif muted:
        edit_reason = "Вы в муте"

    edit_right = BaseRight(
        value=can_edit,
        reason=edit_reason,
        reason_code="edit" if can_edit else "forbidden",
    )

    return ModResponse(
        **public_context.model_dump(exclude_none=True),
        info=BaseRight(
            value=can_read,
            reason="Мод доступен для просмотра" if can_read else "Мод скрыт",
            reason_code="public" if can_read else "hidden",
        ),
        edit=ModEditResponse(
            title=edit_right,
            description=edit_right,
            short_description=edit_right,
            screenshots=edit_right,
            new_version=edit_right,
            authors=BaseRight(
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
        delete=BaseRight(
            value=can_delete,
            reason="Можно удалить мод" if can_delete else "Удаление недоступно",
            reason_code="delete" if can_delete else "forbidden",
        ),
        download=BaseRight(
            value=can_read,
            reason="Мод можно скачать" if can_read else "Скачивание скрыто",
            reason_code="public" if can_read else "hidden",
        ),
    )


@router.put(
    "/mod",
    summary="Get mod add access permissions",
    response_model=ModAddResponse,
    response_model_exclude_none=True,
)
async def mod_add(
    request: Request,
) -> ModAddResponse:
    context = await manager_client.fetch_manager_context(request)
    public_context = context.to_public_context()
    muted = _is_muted(context)

    can_add = False
    add_reason = "Требуется авторизация"
    add_reason_code = "unauthorized"
    can_add_anonymous = False
    anonymous_add_reason = "Требуется авторизация"
    anonymous_add_reason_code = "unauthorized"

    if context.authenticated and context.owner_id >= 0:
        if context.admin:
            can_add = True
            add_reason = "Администратор может публиковать моды"
            add_reason_code = "admin"
            can_add_anonymous = True
            anonymous_add_reason = "Администратор может публиковать моды без автора"
            anonymous_add_reason_code = "admin"
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
        if not context.admin:
            anonymous_add_reason = "Публикация без автора доступна только администратору"
            anonymous_add_reason_code = "admin_required"

    return ModAddResponse(
        **public_context.model_dump(exclude_none=True),
        add=BaseRight(
            value=can_add,
            reason=add_reason,
            reason_code=add_reason_code,
        ),
        anonymous_add=BaseRight(
            value=can_add_anonymous,
            reason=anonymous_add_reason,
            reason_code=anonymous_add_reason_code,
        ),
    )


@router.post(
    "/mod/{mod_id}",
    summary="Get mod access permissions",
    response_model=ModResponse,
    response_model_exclude_none=True,
)
async def mod(
    request: Request,
    payload: ModRequest,
    mod_id: int = Path(..., description="ID мода"),
) -> ModResponse:
    context = await manager_client.fetch_manager_context(request, mod_ids=[mod_id])
    return _mod_response(context, mod_id, payload)


@router.post(
    "/mods",
    summary="Get batch mod access permissions",
    response_model=dict[int, ModResponse],
    response_model_exclude_none=True,
)
async def mods(
    request: Request,
    payload: ModsRequest,
) -> dict[int, ModResponse]:
    context = await manager_client.fetch_manager_context(
        request,
        mod_ids=payload.mods_ids,
    )
    ids = list(dict.fromkeys(int(mod_id) for mod_id in payload.mods_ids))
    return {mod_id: _mod_response(context, mod_id) for mod_id in ids}
