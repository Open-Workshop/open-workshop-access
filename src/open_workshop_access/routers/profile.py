from __future__ import annotations

import datetime

from fastapi import APIRouter, Path, Request

from open_workshop_access import manager_client
from open_workshop_access.contracts.responses import (
    BaseRight,
    ProfileEditResponse,
    ProfileInfoResponse,
    ProfileResponse,
)
from open_workshop_access.contracts.state import AccessState


router = APIRouter()


def _is_muted(context: AccessState) -> bool:
    return bool(context.mute_until and context.mute_until > datetime.datetime.now())


@router.post(
    "/profile/{profile_id}",
    summary="Get profile access permissions",
    response_model=ProfileResponse,
    response_model_exclude_none=True,
)
async def profile(
    request: Request,
    profile_id: int = Path(..., description="ID профиля"),
) -> ProfileResponse:
    context = await manager_client.fetch_manager_context(request)
    now = datetime.datetime.now()
    is_self = context.owner_id >= 0 and context.owner_id == profile_id
    is_admin = bool(context.admin)
    muted = _is_muted(context)
    username_on_cooldown = bool(
        context.username_change_available_at
        and context.username_change_available_at > now
    )

    if is_admin:
        nickname_right = BaseRight(
            value=True,
            reason="Администратор может менять никнейм",
            reason_code="admin",
        )
    elif is_self and context.change_username and not muted and not username_on_cooldown:
        nickname_right = BaseRight(
            value=True,
            reason="Можно менять собственный никнейм",
            reason_code="self",
        )
    elif muted and is_self and context.change_username:
        nickname_right = BaseRight(
            value=False,
            reason="Вы в муте",
            reason_code="muted",
        )
    elif username_on_cooldown and is_self and context.change_username:
        nickname_right = BaseRight(
            value=False,
            reason="Никнейм пока нельзя менять",
            reason_code="cooldown",
        )
    else:
        nickname_right = BaseRight(
            value=False,
            reason="Изменение никнейма недоступно",
            reason_code="forbidden",
        )

    if is_admin:
        description_right = BaseRight(
            value=True,
            reason="Администратор может менять описание",
            reason_code="admin",
        )
    elif is_self and context.change_about and not muted:
        description_right = BaseRight(
            value=True,
            reason="Можно менять собственное описание",
            reason_code="self",
        )
    elif muted and is_self and context.change_about:
        description_right = BaseRight(
            value=False,
            reason="Вы в муте",
            reason_code="muted",
        )
    else:
        description_right = BaseRight(
            value=False,
            reason="Изменение описания недоступно",
            reason_code="forbidden",
        )

    if is_admin:
        avatar_right = BaseRight(
            value=True,
            reason="Администратор может менять аватар",
            reason_code="admin",
        )
    elif is_self and context.change_avatar and not muted:
        avatar_right = BaseRight(
            value=True,
            reason="Можно менять собственный аватар",
            reason_code="self",
        )
    elif muted and is_self and context.change_avatar:
        avatar_right = BaseRight(
            value=False,
            reason="Вы в муте",
            reason_code="muted",
        )
    else:
        avatar_right = BaseRight(
            value=False,
            reason="Изменение аватара недоступно",
            reason_code="forbidden",
        )

    can_vote_for_reputation = bool(context.vote_for_reputation and not muted)
    vote_right = BaseRight(
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
    comments_right = BaseRight(
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
    reactions_right = BaseRight(
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

    return ProfileResponse(
        **context.model_dump(
            exclude={
                "mods",
                "write_comments",
                "set_reactions",
                "vote_for_reputation",
            },
            exclude_none=True,
        ),
        info=ProfileInfoResponse(
            public=BaseRight(
                value=True,
                reason="Профиль доступен для просмотра",
                reason_code="public",
            ),
            meta=BaseRight(
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
        edit=ProfileEditResponse(
            nickname=nickname_right,
            grade=BaseRight(
                value=is_admin,
                reason="Администратор может менять грейд",
                reason_code="admin" if is_admin else "forbidden",
            ),
            description=description_right,
            avatar=avatar_right,
            mute=BaseRight(
                value=is_admin and not is_self,
                reason="Администратор может назначать мут",
                reason_code="admin" if is_admin and not is_self else "forbidden",
            ),
            rights=BaseRight(
                value=is_admin,
                reason="Только администратор может менять права",
                reason_code="admin" if is_admin else "forbidden",
            ),
        ),
        vote_for_reputation=vote_right,
        write_comments=comments_right,
        set_reactions=reactions_right,
        delete=BaseRight(
            value=is_self,
            reason="Удалять можно только свой профиль",
            reason_code="self" if is_self else "forbidden",
        ),
    )
