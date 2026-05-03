from __future__ import annotations

import datetime

from fastapi import APIRouter, Path, Request

from open_workshop_access import manager_client
from open_workshop_access.contracts.requests import ModpackRequest, ModpacksRequest
from open_workshop_access.contracts.responses import (
    BaseRight,
    ModpackAddResponse,
    ModpackEditResponse,
    ModpackResponse,
)
from open_workshop_access.contracts.state import AccessModpackEntry, AccessState


router = APIRouter()


def _is_muted(context: AccessState) -> bool:
    return bool(context.mute_until and context.mute_until > datetime.datetime.now())


def _modpack_entry_by_id(context: AccessState, modpack_id: int) -> AccessModpackEntry | None:
    if not context.modpacks:
        return None
    for modpack in context.modpacks:
        if modpack.modpack_id == modpack_id:
            return modpack
    return None


def _modpack_visibility_reason(
    context: AccessState,
    modpack_entry: AccessModpackEntry | None,
    can_read: bool,
) -> str:
    if can_read:
        if context.admin:
            return "Администратор может просматривать любой модпак."
        if modpack_entry is not None:
            if modpack_entry.owner:
                return "Вы можете просматривать свой модпак."
            if modpack_entry.member:
                return "Вы можете просматривать модпак, где вы указаны соавтором."
            if modpack_entry.public <= 1:
                return "Модпак открыт для просмотра."
        return "Модпак открыт для просмотра."

    if modpack_entry is None:
        return "Модпак скрыт или недоступен для вашей учетной записи."

    return "Этот модпак скрыт для вашей учетной записи."


def _modpack_catalog_reason(
    context: AccessState,
    modpack_entry: AccessModpackEntry | None,
    can_catalog: bool,
) -> str:
    if can_catalog:
        if context.admin:
            return "Администратор может показывать любой модпак в каталоге."
        if modpack_entry is not None:
            if modpack_entry.owner:
                return "Вы можете показывать свой модпак в каталоге."
            if modpack_entry.member:
                return "Вы можете показывать модпак в каталоге как соавтор."
            if modpack_entry.public == 0:
                return "Модпак можно показывать в каталоге."
        return "Модпак можно показывать в каталоге."

    if modpack_entry is None:
        return "Модпак скрыт или недоступен для вашей учетной записи."
    if modpack_entry.condition != 0:
        return "Модпак еще не готов для показа в каталоге."
    if modpack_entry.public > 0:
        return "Этот модпак скрыт из каталога для вашей учетной записи."
    return "Этот модпак скрыт из каталога для вашей учетной записи."


def _modpack_edit_reason(
    context: AccessState,
    modpack_entry: AccessModpackEntry | None,
    can_edit: bool,
    muted: bool,
) -> str:
    if muted:
        return "Редактирование модпака временно недоступно из-за мьюта."
    if context.admin:
        return "Администратор может редактировать любой модпак."
    if modpack_entry is not None:
        if modpack_entry.owner:
            return "Вы можете редактировать свой модпак." if can_edit else "У вас нет права редактировать свой модпак."
        if modpack_entry.member:
            return (
                "Вы можете редактировать модпак как соавтор."
                if can_edit
                else "У вас нет права редактировать этот модпак как соавтор."
            )
    return "У вашей учетной записи нет права редактировать чужие модпаки."


def _modpack_authors_reason(
    context: AccessState,
    modpack_entry: AccessModpackEntry | None,
    payload: ModpackRequest | None,
    can_manage_authors: bool,
    muted: bool,
) -> str:
    if can_manage_authors:
        if context.admin:
            return "Администратор может управлять авторами любого модпака."
        if modpack_entry is not None and modpack_entry.owner:
            return "Вы можете управлять авторами своего модпака."
        if modpack_entry is not None and modpack_entry.member:
            return "Вы можете управлять авторами этого модпака как соавтор."
        return "Эта учетная запись может управлять авторами этого модпака."

    if muted:
        return "Управление авторами модпака временно недоступно из-за мьюта."

    if (
        modpack_entry is not None
        and modpack_entry.owner
        and payload is not None
        and payload.author_id is not None
        and payload.author_id == context.owner_id
        and payload.mode is False
    ):
        return "Владельца нельзя удалять из списка авторов."

    if modpack_entry is not None and modpack_entry.owner:
        return "У вас нет права менять список авторов своего модпака."
    if modpack_entry is not None and modpack_entry.member:
        return "У вас нет права менять список авторов этого модпака как соавтор."
    return "У вашей учетной записи нет права управлять авторами этого модпака."


def _modpack_delete_reason(
    context: AccessState,
    modpack_entry: AccessModpackEntry | None,
    can_delete: bool,
    muted: bool,
) -> str:
    if can_delete:
        if context.admin:
            return "Администратор может удалять любой модпак."
        if modpack_entry is not None and modpack_entry.owner:
            return "Вы можете удалить свой модпак."
        return "Эта учетная запись может удалить этот модпак."

    if muted:
        return "Удаление модпака временно недоступно из-за мьюта."

    if modpack_entry is not None and modpack_entry.owner:
        return "У вас нет права удалить свой модпак."

    return "У вашей учетной записи нет права удалять этот модпак."


def _modpack_response(
    context: AccessState,
    modpack_id: int,
    payload: ModpackRequest | None = None,
) -> ModpackResponse:
    public_context = context.to_public_context()
    modpack_entry = _modpack_entry_by_id(context, modpack_id)
    muted = _is_muted(context)
    is_admin = bool(context.admin)

    can_read = False
    can_catalog = False
    can_edit = False
    can_manage_authors = False
    can_delete = False

    if modpack_entry is not None:
        if is_admin:
            can_read = True
            can_catalog = True
            can_edit = True
            can_manage_authors = True
            can_delete = True
        else:
            if modpack_entry.owner or modpack_entry.member or modpack_entry.public <= 1:
                can_read = True

            if modpack_entry.condition == 0 and (
                modpack_entry.owner
                or modpack_entry.member
                or modpack_entry.public == 0
            ):
                can_catalog = True

            if not muted:
                if modpack_entry.owner or modpack_entry.member:
                    can_edit = bool(context.change_self_modpacks)
                else:
                    can_edit = bool(context.change_modpacks)

                if payload is not None:
                    if modpack_entry.owner:
                        can_manage_authors = not (
                            payload.author_id is not None
                            and payload.author_id == context.owner_id
                            and payload.mode is False
                        )
                    elif modpack_entry.member:
                        can_manage_authors = (
                            payload.author_id is not None
                            and payload.author_id == context.owner_id
                            and payload.mode is False
                        )
                    else:
                        can_manage_authors = bool(context.change_authorship_modpacks)
                else:
                    can_manage_authors = bool(context.change_authorship_modpacks)

                if modpack_entry.owner and context.delete_self_modpacks:
                    can_delete = True
                else:
                    can_delete = bool(context.delete_modpacks)

    edit_right = BaseRight(
        value=can_edit,
        reason=_modpack_edit_reason(context, modpack_entry, can_edit, muted),
        reason_code="edit" if can_edit else "forbidden",
    )

    return ModpackResponse(
        **public_context.model_dump(exclude_none=True),
        info=BaseRight(
            value=can_read,
            reason=_modpack_visibility_reason(context, modpack_entry, can_read),
            reason_code="public" if can_read else "hidden",
        ),
        catalog=BaseRight(
            value=can_catalog,
            reason=_modpack_catalog_reason(context, modpack_entry, can_catalog),
            reason_code="catalog" if can_catalog else "hidden",
        ),
        edit=ModpackEditResponse(
            title=edit_right,
            description=edit_right,
            short_description=edit_right,
            authors=BaseRight(
                value=can_manage_authors,
                reason=_modpack_authors_reason(
                    context, modpack_entry, payload, can_manage_authors, muted
                ),
                reason_code="authors" if can_manage_authors else "forbidden",
            ),
        ),
        delete=BaseRight(
            value=can_delete,
            reason=_modpack_delete_reason(context, modpack_entry, can_delete, muted),
            reason_code="delete" if can_delete else "forbidden",
        ),
    )


@router.put(
    "/modpack",
    summary="Get modpack add access permissions",
    response_model=ModpackAddResponse,
    response_model_exclude_none=True,
)
async def modpack_add(request: Request) -> ModpackAddResponse:
    context = await manager_client.fetch_manager_context(request)
    public_context = context.to_public_context()
    muted = _is_muted(context)

    can_add = False
    add_reason = "Войдите в аккаунт, чтобы публиковать модпаки."
    add_reason_code = "unauthorized"
    can_add_anonymous = False
    anonymous_add_reason = "Войдите в аккаунт, чтобы публиковать модпак без автора."
    anonymous_add_reason_code = "unauthorized"

    if context.authenticated and context.owner_id >= 0:
        if context.admin:
            can_add = True
            add_reason = "Администратор может публиковать модпаки."
            add_reason_code = "admin"
            can_add_anonymous = True
            anonymous_add_reason = "Администратор может публиковать модпаки без автора."
            anonymous_add_reason_code = "admin"
        elif muted:
            add_reason = "Публикация модпаков временно запрещена из-за мьюта."
            add_reason_code = "muted"
        elif context.publish_modpacks:
            can_add = True
            add_reason = "Вы можете публиковать модпаки."
            add_reason_code = "allowed"
        else:
            add_reason = "У вашей учетной записи нет права публиковать модпаки."
            add_reason_code = "forbidden"
        if not context.admin:
            anonymous_add_reason = "Публиковать модпак без автора может только администратор."
            anonymous_add_reason_code = "admin_required"

    return ModpackAddResponse(
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
    "/modpack/{modpack_id}",
    summary="Get modpack access permissions",
    response_model=ModpackResponse,
    response_model_exclude_none=True,
)
async def modpack(
    request: Request,
    payload: ModpackRequest,
    modpack_id: int = Path(..., description="ID модпака"),
) -> ModpackResponse:
    context = await manager_client.fetch_manager_context(request, modpack_ids=[modpack_id])
    return _modpack_response(context, modpack_id, payload)


@router.post(
    "/modpacks",
    summary="Get batch modpack access permissions",
    response_model=dict[int, ModpackResponse],
    response_model_exclude_none=True,
)
async def modpacks(
    request: Request,
    payload: ModpacksRequest,
) -> dict[int, ModpackResponse]:
    context = await manager_client.fetch_manager_context(
        request,
        modpack_ids=payload.modpacks_ids,
    )
    ids = list(dict.fromkeys(int(modpack_id) for modpack_id in payload.modpacks_ids))
    modpack_payload = (
        ModpackRequest(author_id=payload.author_id, mode=payload.mode)
        if payload.author_id is not None or payload.mode is not None
        else None
    )
    return {modpack_id: _modpack_response(context, modpack_id, modpack_payload) for modpack_id in ids}
