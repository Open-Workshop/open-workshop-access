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
    "owner_id": 7,
    "login_method": "password",
    "mute_until": "2026-02-07T18:20:45",
    "last_username_reset": "2026-02-07T18:20:45",
    "last_password_reset": "2026-02-07T18:15:45",
    "password_change_available_at": "2026-02-07T18:20:45",
    "username_change_available_at": "2026-03-09T18:20:45",
}

ACCESS_STATE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "admin": False,
    "write_comments": True,
    "set_reactions": True,
    "create_reactions": False,
    "mute_users": False,
    "publish_mods": True,
    "change_authorship_mods": False,
    "change_self_mods": True,
    "change_mods": False,
    "delete_self_mods": True,
    "delete_mods": False,
    "create_forums": True,
    "change_authorship_forums": False,
    "change_self_forums": True,
    "change_forums": False,
    "delete_self_forums": True,
    "delete_forums": False,
    "change_username": True,
    "change_about": True,
    "change_avatar": True,
    "vote_for_reputation": True,
    "mods": [ACCESS_MOD_ENTRY_EXAMPLE],
}

ACCESS_PUBLIC_CONTEXT_FIELDS: tuple[str, ...] = (
    "authenticated",
    "owner_id",
    "login_method",
    "mute_until",
    "last_username_reset",
    "last_password_reset",
    "password_change_available_at",
    "username_change_available_at",
)


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
    owner_id: int = -1
    login_method: str | None = None

    mute_until: datetime | None = None

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

    admin: bool = False
    write_comments: bool = False
    set_reactions: bool = False
    create_reactions: bool = False
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

    mods: list[AccessModEntry] | None = None

    def to_public_context(self) -> AccessContext:
        public_payload = {
            field: getattr(self, field)
            for field in ACCESS_PUBLIC_CONTEXT_FIELDS
        }
        return AccessContext.model_validate(public_payload)
