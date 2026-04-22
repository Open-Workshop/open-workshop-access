from __future__ import annotations

from open_workshop_access.contracts.state import AccessModel


class ModRequest(AccessModel):
    author_id: int | None = None
    mode: bool | None = None


class ModsRequest(AccessModel):
    mods_ids: list[int]
    edit: bool = False
