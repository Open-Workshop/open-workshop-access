from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from open_workshop_access.contracts.state import ACCESS_CONTEXT_EXAMPLE, AccessContext


BASE_RIGHT_EXAMPLE = {
    "value": True,
    "reason": "Это право доступно этой учетной записи",
    "reason_code": "allowed",
}

CATALOG_RIGHT_EXAMPLE = {
    "value": True,
    "reason": "Мод можно показывать в каталоге",
    "reason_code": "catalog",
}

BASE_RIGHT_FORBIDDEN_EXAMPLE = {
    "value": False,
    "reason": "Для этого действия требуются дополнительные права",
    "reason_code": "admin_required",
}

CRUD_RIGHT_EXAMPLE = {
    "value": True,
    "reason": "Администратор может управлять этим разделом",
    "reason_code": "admin",
}

MOD_EDIT_RESPONSE_EXAMPLE = {
    "title": BASE_RIGHT_EXAMPLE,
    "description": BASE_RIGHT_EXAMPLE,
    "short_description": BASE_RIGHT_EXAMPLE,
    "screenshots": BASE_RIGHT_EXAMPLE,
    "new_version": BASE_RIGHT_EXAMPLE,
    "authors": BASE_RIGHT_EXAMPLE,
    "tags": BASE_RIGHT_EXAMPLE,
    "dependencies": BASE_RIGHT_EXAMPLE,
}

MODPACK_EDIT_RESPONSE_EXAMPLE = {
    "title": BASE_RIGHT_EXAMPLE,
    "description": BASE_RIGHT_EXAMPLE,
    "short_description": BASE_RIGHT_EXAMPLE,
    "authors": BASE_RIGHT_EXAMPLE,
}

GAME_EDIT_RESPONSE_EXAMPLE = {
    "title": CRUD_RIGHT_EXAMPLE,
    "description": CRUD_RIGHT_EXAMPLE,
    "short_description": CRUD_RIGHT_EXAMPLE,
    "screenshots": CRUD_RIGHT_EXAMPLE,
    "tags": CRUD_RIGHT_EXAMPLE,
    "genres": CRUD_RIGHT_EXAMPLE,
}

PROFILE_INFO_RESPONSE_EXAMPLE = {
    "public": BASE_RIGHT_EXAMPLE,
    "meta": BASE_RIGHT_EXAMPLE,
}

PROFILE_EDIT_RESPONSE_EXAMPLE = {
    "nickname": BASE_RIGHT_EXAMPLE,
    "grade": CRUD_RIGHT_EXAMPLE,
    "description": BASE_RIGHT_EXAMPLE,
    "avatar": BASE_RIGHT_EXAMPLE,
    "mute": CRUD_RIGHT_EXAMPLE,
    "password": BASE_RIGHT_EXAMPLE,
    "rights": CRUD_RIGHT_EXAMPLE,
}

MOD_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "info": BASE_RIGHT_EXAMPLE,
    "catalog": CATALOG_RIGHT_EXAMPLE,
    "edit": MOD_EDIT_RESPONSE_EXAMPLE,
    "delete": BASE_RIGHT_EXAMPLE,
    "download": BASE_RIGHT_EXAMPLE,
}

MODPACK_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "info": BASE_RIGHT_EXAMPLE,
    "catalog": CATALOG_RIGHT_EXAMPLE,
    "edit": MODPACK_EDIT_RESPONSE_EXAMPLE,
    "delete": BASE_RIGHT_EXAMPLE,
}

MOD_ADD_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "add": BASE_RIGHT_EXAMPLE,
    "anonymous_add": BASE_RIGHT_FORBIDDEN_EXAMPLE,
}

MODPACK_ADD_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "add": BASE_RIGHT_EXAMPLE,
    "anonymous_add": BASE_RIGHT_FORBIDDEN_EXAMPLE,
}

SIMPLE_CRUD_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "add": CRUD_RIGHT_EXAMPLE,
    "edit": CRUD_RIGHT_EXAMPLE,
    "delete": CRUD_RIGHT_EXAMPLE,
}

GAME_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "edit": GAME_EDIT_RESPONSE_EXAMPLE,
    "delete": CRUD_RIGHT_EXAMPLE,
}

GAME_ADD_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "add": CRUD_RIGHT_EXAMPLE,
}

PROFILE_RESPONSE_EXAMPLE = {
    **ACCESS_CONTEXT_EXAMPLE,
    "info": PROFILE_INFO_RESPONSE_EXAMPLE,
    "edit": PROFILE_EDIT_RESPONSE_EXAMPLE,
    "vote_for_reputation": BASE_RIGHT_EXAMPLE,
    "write_comments": BASE_RIGHT_EXAMPLE,
    "set_reactions": BASE_RIGHT_EXAMPLE,
    "delete": BASE_RIGHT_EXAMPLE,
}


class BaseRight(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": BASE_RIGHT_EXAMPLE})

    value: bool
    reason: str
    reason_code: str


class ModEditResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": MOD_EDIT_RESPONSE_EXAMPLE})

    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    screenshots: BaseRight
    new_version: BaseRight
    authors: BaseRight
    tags: BaseRight
    dependencies: BaseRight


class ModpackEditResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": MODPACK_EDIT_RESPONSE_EXAMPLE})

    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    authors: BaseRight


class ModResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": MOD_RESPONSE_EXAMPLE})

    info: BaseRight
    catalog: BaseRight
    edit: ModEditResponse
    delete: BaseRight
    download: BaseRight


class ModpackResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": MODPACK_RESPONSE_EXAMPLE})

    info: BaseRight
    catalog: BaseRight
    edit: ModpackEditResponse
    delete: BaseRight


class ModAddResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": MOD_ADD_RESPONSE_EXAMPLE})

    add: BaseRight
    anonymous_add: BaseRight


class ModpackAddResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": MODPACK_ADD_RESPONSE_EXAMPLE})

    add: BaseRight
    anonymous_add: BaseRight


class SimpleCrudResponse(AccessContext):
    model_config = ConfigDict(
        json_schema_extra={"example": SIMPLE_CRUD_RESPONSE_EXAMPLE}
    )

    add: BaseRight
    edit: BaseRight
    delete: BaseRight


class GameEditResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": GAME_EDIT_RESPONSE_EXAMPLE})

    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    screenshots: BaseRight
    tags: BaseRight
    genres: BaseRight


class GameResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": GAME_RESPONSE_EXAMPLE})

    edit: GameEditResponse
    delete: BaseRight


class GameAddResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": GAME_ADD_RESPONSE_EXAMPLE})

    add: BaseRight


class ProfileInfoResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": PROFILE_INFO_RESPONSE_EXAMPLE}
    )

    public: BaseRight
    meta: BaseRight


class ProfileEditResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": PROFILE_EDIT_RESPONSE_EXAMPLE}
    )

    nickname: BaseRight
    grade: BaseRight
    description: BaseRight
    avatar: BaseRight
    mute: BaseRight
    password: BaseRight
    rights: BaseRight


class ProfileResponse(AccessContext):
    model_config = ConfigDict(json_schema_extra={"example": PROFILE_RESPONSE_EXAMPLE})

    info: ProfileInfoResponse
    edit: ProfileEditResponse
    vote_for_reputation: BaseRight
    write_comments: BaseRight
    set_reactions: BaseRight
    delete: BaseRight
