from pydantic import BaseModel


# MOD

class ModEditResponse(BaseModel):
    title: bool
    description: bool
    short_description: bool
    screenshots: bool
    new_version: bool
    authors: bool
    tags: bool
    dependencies: bool


class ModResponse(BaseModel):
    info: bool
    edit: ModEditResponse
    delete: bool
    download: bool


# TAG / GENRE

class SimpleCrudResponse(BaseModel):
    add: bool
    edit: bool
    delete: bool


# GAME

class GameEditResponse(BaseModel):
    title: bool
    description: bool
    short_description: bool
    screenshots: bool
    tags: bool
    genres: bool


class GameResponse(BaseModel):
    edit: GameEditResponse
    delete: bool


# PROFILE

class ProfileInfoResponse(BaseModel):
    public: bool
    meta: bool


class ProfileEditResponse(BaseModel):
    nickname: bool
    grade: bool
    description: bool
    avatar: bool
    mute: bool
    rights: bool


class ProfileResponse(BaseModel):
    info: ProfileInfoResponse
    edit: ProfileEditResponse
    vote_for_reputation: bool
    write_comments: bool
    set_reactions: bool
    delete: bool


# Ошибка

class ErrorDetailResponse(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetailResponse
