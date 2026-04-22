from __future__ import annotations

from pydantic import ConfigDict

from open_workshop_access.contracts.state import AccessModel


class ModRequest(AccessModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"author_id": 15, "mode": False}}
    )

    author_id: int | None = None
    mode: bool | None = None


class ModsRequest(AccessModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"mods_ids": [1, 2, 3]}}
    )

    mods_ids: list[int]
