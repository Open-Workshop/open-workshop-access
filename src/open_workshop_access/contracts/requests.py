from __future__ import annotations

from pydantic import Field

from open_workshop_access.contracts.state import AccessModel


class ContextRequest(AccessModel):
    user_id: int | None = None


class ModAddRequest(AccessModel):
    without_author: bool = False


class ModRequest(AccessModel):
    author_id: int | None = None
    mode: bool | None = None


class ModsRequest(AccessModel):
    user_id: int | None = None
    mods_ids: list[int] = Field(default_factory=list)
    edit: bool = False

