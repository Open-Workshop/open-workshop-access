from pydantic import BaseModel


class BaseRight(BaseModel):
    value: bool
    reason: str
    """
    Примеры:
    1. Вы в муте (value==false)
    2. Вы админ (value==true)
    """
    reason_code: str
    """
    Примеры:
    1. in_mute (value==false)
    2. admin (value==true)
    """


# MOD

class ModEditResponse(BaseModel):
    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    screenshots: BaseRight
    new_version: BaseRight
    authors: BaseRight
    tags: BaseRight
    dependencies: BaseRight


class ModResponse(BaseModel):
    info: BaseRight
    edit: ModEditResponse
    delete: BaseRight
    download: BaseRight


# TAG / GENRE

class SimpleCrudResponse(BaseModel):
    add: BaseRight
    edit: BaseRight
    delete: BaseRight


# GAME

class GameEditResponse(BaseModel):
    title: BaseRight
    description: BaseRight
    short_description: BaseRight
    screenshots: BaseRight
    tags: BaseRight
    genres: BaseRight


class GameResponse(BaseModel):
    edit: GameEditResponse
    delete: BaseRight


# PROFILE

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


class ProfileResponse(BaseModel):
    info: ProfileInfoResponse
    edit: ProfileEditResponse
    vote_for_reputation: BaseRight
    write_comments: BaseRight
    set_reactions: BaseRight
    delete: BaseRight


# Ошибка

class ErrorDetailResponse(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetailResponse
