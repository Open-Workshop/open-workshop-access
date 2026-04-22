from __future__ import annotations

from pydantic import BaseModel, Field

from open_workshop_access.contracts.state import AccessState


class BaseRight(BaseModel):
    value: bool
    reason: str
    reason_code: str


class ModEditResponse(BaseModel):
    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    screenshots: BaseRight
    new_version: BaseRight
    authors: BaseRight
    tags: BaseRight
    dependencies: BaseRight


class ModResponse(AccessState):
    info: BaseRight
    edit: ModEditResponse
    delete: BaseRight
    download: BaseRight


class ModAddResponse(AccessState):
    add: BaseRight


class ModsResponse(AccessState):
    allowed_ids: list[int] = Field(default_factory=list)


class SimpleCrudResponse(AccessState):
    add: BaseRight
    edit: BaseRight
    delete: BaseRight


class GameEditResponse(BaseModel):
    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    screenshots: BaseRight
    tags: BaseRight
    genres: BaseRight


class GameResponse(AccessState):
    edit: GameEditResponse
    delete: BaseRight


class GameAddResponse(AccessState):
    add: BaseRight


class ProfileInfoResponse(BaseModel):
    public: BaseRight
    meta: BaseRight


class ProfileEditResponse(BaseModel):
    nickname: BaseRight
    grade: BaseRight
    description: BaseRight
    avatar: BaseRight
    mute: BaseRight
    rights: BaseRight


class ProfileResponse(AccessState):
    info: ProfileInfoResponse
    edit: ProfileEditResponse
    vote_for_reputation: BaseRight
    write_comments: BaseRight
    set_reactions: BaseRight
    delete: BaseRight

