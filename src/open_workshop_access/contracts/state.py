from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


ACCESS_MOD_ENTRY_EXAMPLE = {
    "mod_id": 1,
    "public": 0,
    "condition": 0,
    "owner": True,
    "member": False,
}

ACCESS_CONTEXT_EXAMPLE = {
    "authenticated": True,
    "login_method": "password",
}

ACCESS_STATE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "owner_id": 7,
    "admin": False,
    "publish_mods": True,
    "change_self_mods": True,
    "mods": [ACCESS_MOD_ENTRY_EXAMPLE],
}


class AccessModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class AccessModEntry(AccessModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        json_schema_extra={"example": ACCESS_MOD_ENTRY_EXAMPLE},
    )

    mod_id: int
    public: int = 0
    condition: int = 0
    owner: bool = False
    member: bool = False


class AccessContext(AccessModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        json_schema_extra={"example": ACCESS_CONTEXT_EXAMPLE},
    )

    authenticated: bool = False
    login_method: str | None = None

    write_comments: bool = False
    set_reactions: bool = False
    create_reactions: bool = False
    mute_until: datetime | None = None
    mute_users: bool = False

    change_authorship_mods: bool = False
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


class AccessState(AccessContext):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        json_schema_extra={"example": ACCESS_STATE_EXAMPLE},
    )

    owner_id: int = -1
    admin: bool = False
    publish_mods: bool = False
    change_self_mods: bool = False
    mods: list[AccessModEntry] | None = None
