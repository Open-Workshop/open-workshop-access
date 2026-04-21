from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class AccountModel(BaseModel):
    """Модель аккаунта пользователя."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    last_username_reset: datetime | None = None
    registration_date: datetime | None = None

    # Глобальные права
    admin: bool = Field(
        default=False,
        description=(
            "Полные административные права. "
            "Админ может менять грейды у всех пользователей, "
            "назначать новых админов и выдавать права."
        ),
    )

    # Социальные действия
    write_comments: bool = Field(
        default=False,
        description="Право писать и редактировать комментарии.",
    )
    set_reactions: bool = Field(
        default=False,
        description="Право ставить реакции.",
    )
    create_reactions: bool = Field(
        default=False,
        description="Право создавать новые реакции.",
    )
    mute_until: datetime | None = Field(
        default=None,
        description=(
            "Временная блокировка социальных действий. "
            "Активна, если это время больше текущего."
        ),
    )
    mute_users: bool = Field(
        default=False,
        description="Право мутить пользователей.",
    )

    # Права на моды
    publish_mods: bool = Field(default=False)
    change_authorship_mods: bool = Field(default=False)
    change_self_mods: bool = Field(default=False)
    change_mods: bool = Field(default=False)
    delete_self_mods: bool = Field(default=False)
    delete_mods: bool = Field(default=False)

    # Права на форумы
    create_forums: bool = Field(default=False)
    change_authorship_forums: bool = Field(default=False)
    change_self_forums: bool = Field(default=False)
    change_forums: bool = Field(default=False)
    delete_self_forums: bool = Field(default=False)
    delete_forums: bool = Field(default=False)

    # Права на профиль
    change_username: bool = Field(default=False)
    change_about: bool = Field(default=False)
    change_avatar: bool = Field(default=False)

    # Репутация
    vote_for_reputation: bool = Field(default=False)