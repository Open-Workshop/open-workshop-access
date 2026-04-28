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


def _forbidden_reason(action: str) -> str:
    return f"У этой учетной записи нет права {action}."


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
    public_context = context.to_public_context()
    now = datetime.datetime.now()
    is_self = context.owner_id >= 0 and context.owner_id == profile_id
    is_admin = bool(context.admin)
    muted = _is_muted(context)
    username_on_cooldown = bool(
        context.username_change_available_at
        and context.username_change_available_at > now
    )
    password_on_cooldown = bool(
        context.password_change_available_at
        and context.password_change_available_at > now
    )

    if is_admin:
        nickname_right = BaseRight(
            value=True,
            reason="Администратор может менять никнейм пользователя.",
            reason_code="admin",
        )
    elif is_self and context.change_username and not muted and not username_on_cooldown:
        nickname_right = BaseRight(
            value=True,
            reason="Вы можете менять свой никнейм.",
            reason_code="self",
        )
    elif muted and is_self and context.change_username:
        nickname_right = BaseRight(
            value=False,
            reason="Смена никнейма временно недоступна из-за мьюта.",
            reason_code="muted",
        )
    elif username_on_cooldown and is_self and context.change_username:
        nickname_right = BaseRight(
            value=False,
            reason="Смена никнейма пока недоступна: после последнего изменения действует задержка.",
            reason_code="cooldown",
        )
    else:
        nickname_right = BaseRight(
            value=False,
            reason=_forbidden_reason("менять никнейм"),
            reason_code="forbidden",
        )

    if is_admin:
        description_right = BaseRight(
            value=True,
            reason="Администратор может менять описание пользователя.",
            reason_code="admin",
        )
    elif is_self and context.change_about and not muted:
        description_right = BaseRight(
            value=True,
            reason="Вы можете менять своё описание.",
            reason_code="self",
        )
    elif muted and is_self and context.change_about:
        description_right = BaseRight(
            value=False,
            reason="Изменение описания временно недоступно из-за мьюта.",
            reason_code="muted",
        )
    else:
        description_right = BaseRight(
            value=False,
            reason=_forbidden_reason("менять описание"),
            reason_code="forbidden",
        )

    if is_admin:
        avatar_right = BaseRight(
            value=True,
            reason="Администратор может менять аватар пользователя.",
            reason_code="admin",
        )
    elif is_self and context.change_avatar and not muted:
        avatar_right = BaseRight(
            value=True,
            reason="Вы можете менять свой аватар.",
            reason_code="self",
        )
    elif muted and is_self and context.change_avatar:
        avatar_right = BaseRight(
            value=False,
            reason="Изменение аватара временно недоступно из-за мьюта.",
            reason_code="muted",
        )
    else:
        avatar_right = BaseRight(
            value=False,
            reason=_forbidden_reason("менять аватар"),
            reason_code="forbidden",
        )

    if is_admin and is_self:
        password_right = BaseRight(
            value=True,
            reason="Администратор может менять свой пароль.",
            reason_code="admin",
        )
    elif is_self and not muted and not password_on_cooldown:
        password_right = BaseRight(
            value=True,
            reason="Вы можете менять свой пароль.",
            reason_code="self",
        )
    elif muted and is_self:
        password_right = BaseRight(
            value=False,
            reason="Смена пароля временно недоступна из-за мьюта.",
            reason_code="muted",
        )
    elif password_on_cooldown and is_self:
        password_right = BaseRight(
            value=False,
            reason="Смена пароля пока недоступна: после последнего изменения действует задержка.",
            reason_code="cooldown",
        )
    else:
        password_right = BaseRight(
            value=False,
            reason=_forbidden_reason("менять пароль"),
            reason_code="forbidden",
        )

    can_vote_for_reputation = bool(context.vote_for_reputation and not muted)
    vote_right = BaseRight(
        value=can_vote_for_reputation,
        reason=(
            "Голосование за репутацию доступно этой учетной записи."
            if can_vote_for_reputation
            else "Голосование за репутацию временно недоступно из-за мьюта."
            if muted
            else _forbidden_reason("голосовать за репутацию")
        ),
        reason_code="allowed" if can_vote_for_reputation else "muted" if muted else "forbidden",
    )
    can_write_comments = bool(context.write_comments and not muted)
    comments_right = BaseRight(
        value=can_write_comments,
        reason=(
            "Комментирование доступно этой учетной записи."
            if can_write_comments
            else "Комментирование временно недоступно из-за мьюта."
            if muted
            else _forbidden_reason("писать комментарии")
        ),
        reason_code="allowed" if can_write_comments else "muted" if muted else "forbidden",
    )
    can_set_reactions = bool(context.set_reactions and not muted)
    reactions_right = BaseRight(
        value=can_set_reactions,
        reason=(
            "Постановка реакций доступна этой учетной записи."
            if can_set_reactions
            else "Постановка реакций временно недоступна из-за мьюта."
            if muted
            else _forbidden_reason("ставить реакции")
        ),
        reason_code="allowed" if can_set_reactions else "muted" if muted else "forbidden",
    )

    return ProfileResponse(
        **public_context.model_dump(exclude_none=True),
        info=ProfileInfoResponse(
            public=BaseRight(
                value=True,
                reason="Профиль открыт для просмотра.",
                reason_code="public",
            ),
            meta=BaseRight(
                value=is_admin or is_self,
                reason=(
                    "Это ваш профиль, скрытые данные доступны."
                    if is_self
                    else "Вы администратор и видите скрытые данные профиля."
                    if is_admin
                    else "Скрытые данные профиля недоступны этой учетной записи."
                ),
                reason_code="self" if is_self else "admin" if is_admin else "forbidden",
            ),
        ),
        edit=ProfileEditResponse(
            nickname=nickname_right,
            grade=BaseRight(
                value=is_admin,
                reason="Администратор может менять грейд пользователя.",
                reason_code="admin" if is_admin else "forbidden",
            ),
            description=description_right,
            avatar=avatar_right,
            mute=BaseRight(
                value=is_admin and not is_self,
                reason=(
                    "Администратор может назначать мут пользователю."
                    if is_admin and not is_self
                    else "Администратор не может назначить мут своему профилю."
                    if is_admin
                    else "Нельзя назначить мут своему профилю."
                    if is_self
                    else "У этой учетной записи нет права назначать мут."
                ),
                reason_code="admin" if is_admin and not is_self else "forbidden",
            ),
            password=password_right,
            rights=BaseRight(
                value=is_admin,
                reason="Администратор может менять права пользователя.",
                reason_code="admin" if is_admin else "forbidden",
            ),
        ),
        vote_for_reputation=vote_right,
        write_comments=comments_right,
        set_reactions=reactions_right,
        delete=BaseRight(
            value=is_self,
            reason="Вы можете удалить свой профиль." if is_self else "Удалить можно только свой профиль.",
            reason_code="self" if is_self else "forbidden",
        ),
    )
