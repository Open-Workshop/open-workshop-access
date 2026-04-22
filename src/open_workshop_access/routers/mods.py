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


def _mod_visibility_reason(context: AccessState, mod_entry: AccessModEntry | None, can_read: bool) -> str:
    if can_read:
        if context.admin:
            return "Администратор может просматривать любой мод."
        if mod_entry is not None:
            if mod_entry.owner:
                return "Вы можете просматривать свой мод."
            if mod_entry.member:
                return "Вы можете просматривать мод, где вы указаны соавтором."
            if mod_entry.public <= 1:
                return "Мод открыт для просмотра."
        return "Мод открыт для просмотра."

    if mod_entry is None:
        return "Мод скрыт или недоступен для вашей учетной записи."

    return "Этот мод скрыт для вашей учетной записи."


def _mod_edit_reason(
    context: AccessState,
    mod_entry: AccessModEntry | None,
    can_edit: bool,
    muted: bool,
) -> str:
    if muted:
        return "Редактирование мода временно недоступно из-за мьюта."
    if context.admin:
        return "Администратор может редактировать любой мод."
    if mod_entry is not None:
        if mod_entry.owner:
            return "Вы можете редактировать свой мод." if can_edit else "У вас нет права редактировать свой мод."
        if mod_entry.member:
            return "Вы можете редактировать мод как соавтор." if can_edit else "У вас нет права редактировать этот мод как соавтор."
    return "У вашей учетной записи нет права редактировать чужие моды."


def _mod_authors_reason(
    context: AccessState,
    mod_entry: AccessModEntry | None,
    payload: ModRequest | None,
    can_manage_authors: bool,
    muted: bool,
) -> str:
    if can_manage_authors:
        if context.admin:
            return "Администратор может управлять авторами любого мода."
        if mod_entry is not None and mod_entry.owner:
            return "Вы можете управлять авторами своего мода."
        if mod_entry is not None and mod_entry.member:
            return "Вы можете управлять авторами этого мода как соавтор."
        return "Эта учетная запись может управлять авторами этого мода."

    if muted:
        return "Управление авторами мода временно недоступно из-за мьюта."

    if (
        mod_entry is not None
        and mod_entry.owner
        and payload is not None
        and payload.author_id is not None
        and payload.author_id == context.owner_id
        and payload.mode is False
    ):
        return "Владельца нельзя удалять из списка авторов."

    if mod_entry is not None and mod_entry.owner:
        return "У вас нет права менять список авторов своего мода."
    if mod_entry is not None and mod_entry.member:
        return "У вас нет права менять список авторов этого мода как соавтор."
    return "У вашей учетной записи нет права управлять авторами этого мода."


def _mod_delete_reason(
    context: AccessState,
    mod_entry: AccessModEntry | None,
    can_delete: bool,
    muted: bool,
) -> str:
    if can_delete:
        if context.admin:
            return "Администратор может удалять любой мод."
        if mod_entry is not None and mod_entry.owner:
            return "Вы можете удалить свой мод."
        return "Эта учетная запись может удалить этот мод."

    if muted:
        return "Удаление мода временно недоступно из-за мьюта."

    if mod_entry is not None and mod_entry.owner:
        return "У вас нет права удалить свой мод."

    return "У вашей учетной записи нет права удалять этот мод."


def _mod_download_reason(mod_entry: AccessModEntry | None, can_read: bool) -> str:
    if can_read:
        return "Мод доступен для скачивания."
    if mod_entry is None:
        return "Мод скрыт или недоступен для вашей учетной записи."
    return "Этот мод скрыт для вашей учетной записи, поэтому скачивание недоступно."


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
                if mod_entry.owner or mod_entry.member:
                    can_edit = bool(context.change_self_mods)
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

    edit_right = BaseRight(
        value=can_edit,
        reason=_mod_edit_reason(context, mod_entry, can_edit, muted),
        reason_code="edit" if can_edit else "forbidden",
    )

    return ModResponse(
        **public_context.model_dump(exclude_none=True),
        info=BaseRight(
            value=can_read,
            reason=_mod_visibility_reason(context, mod_entry, can_read),
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
                reason=_mod_authors_reason(context, mod_entry, payload, can_manage_authors, muted),
                reason_code="authors" if can_manage_authors else "forbidden",
            ),
            tags=edit_right,
            dependencies=edit_right,
        ),
        delete=BaseRight(
            value=can_delete,
            reason=_mod_delete_reason(context, mod_entry, can_delete, muted),
            reason_code="delete" if can_delete else "forbidden",
        ),
        download=BaseRight(
            value=can_read,
            reason=_mod_download_reason(mod_entry, can_read),
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
    add_reason = "Войдите в аккаунт, чтобы публиковать моды."
    add_reason_code = "unauthorized"
    can_add_anonymous = False
    anonymous_add_reason = "Войдите в аккаунт, чтобы публиковать мод без автора."
    anonymous_add_reason_code = "unauthorized"

    if context.authenticated and context.owner_id >= 0:
        if context.admin:
            can_add = True
            add_reason = "Администратор может публиковать моды."
            add_reason_code = "admin"
            can_add_anonymous = True
            anonymous_add_reason = "Администратор может публиковать моды без автора."
            anonymous_add_reason_code = "admin"
        elif muted:
            add_reason = "Публикация модов временно запрещена из-за мьюта."
            add_reason_code = "muted"
        elif context.publish_mods:
            can_add = True
            add_reason = "Вы можете публиковать моды."
            add_reason_code = "allowed"
        else:
            add_reason = "У вашей учетной записи нет права публиковать моды."
            add_reason_code = "forbidden"
        if not context.admin:
            anonymous_add_reason = "Публиковать мод без автора может только администратор."
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
    mod_payload = (
        ModRequest(author_id=payload.author_id, mode=payload.mode)
        if payload.author_id is not None or payload.mode is not None
        else None
    )
    return {mod_id: _mod_response(context, mod_id, mod_payload) for mod_id in ids}
