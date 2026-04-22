from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AccessModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class AccessModEntry(AccessModel):
    mod_id: int
    public: int = 0
    condition: int = 0
    owner: bool = False
    member: bool = False


class AccessRequest(AccessModel):
    access_token: str | None = None
    refresh_token: str | None = None
    user_id: int | None = None
    mods_ids: list[int] = Field(default_factory=list)
    mod_id: int | None = None
    profile_id: int | None = None
    author_id: int | None = None
    mode: bool | None = None
    without_author: bool | None = None
    edit: bool = False


class AccessState(AccessModel):
    authenticated: bool = False
    owner_id: int = -1
    login_method: str | None = None

    admin: bool = False
    write_comments: bool = False
    set_reactions: bool = False
    create_reactions: bool = False
    mute_until: datetime | None = None
    mute_users: bool = False

    publish_mods: bool = False
    change_authorship_mods: bool = False
    change_self_mods: bool = False
    change_mods: bool = False
    delete_self_mods: bool = False
    delete_mods: bool = False

    create_forums: bool = False
    change_authorship_forums: bool = False
    change_self_forums: bool = False
    change_forums: bool = False
    delete_self_forums: bool = False
    delete_forums: bool = False

    change_username: bool = False
    change_about: bool = False
    change_avatar: bool = False
    vote_for_reputation: bool = False

    last_username_reset: datetime | None = None
    last_password_reset: datetime | None = None
    password_change_available_at: datetime | None = None
    username_change_available_at: datetime | None = None

    mods: list[AccessModEntry] | None = None
