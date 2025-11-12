from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class UserInfo(BaseModel):
    username: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    web_url: str


class GitlabProject(BaseModel):
    id: int
    name_with_namespace: str
    path_with_namespace: str
    web_url: str
    access_level: int
    bot_id: Optional[int] = None
    bot_name: Optional[str] = None
    avatar_url: Optional[str] = None
