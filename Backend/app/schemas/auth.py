from typing import Optional
from pydantic import BaseModel


class RefreshTokenIn(BaseModel):
    refresh_token: str


class RefreshTokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserInfo(BaseModel):
    id: int
    email: str
    username: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_superuser: bool


class GitlabAuthUrl(BaseModel):
    url: str


