from typing import Optional, List
from pydantic import BaseModel, Field


# ---- Create ----
class BotCreate(BaseModel):
    gitlab_project_path: str
    gitlab_access_token: str
    llm_name: str


# ---- Read ----
class BotRead(BaseModel):
    id: int
    gitlab_project_path: str
    gitlab_access_token: str
    gitlab_access_token_name: str
    gitlab_webhook_id: Optional[int] = None
    gitlab_webhook_secret: Optional[str] = None
    gitlab_scopes: List[str] = Field(default_factory=list)
    gitlab_access_level: Optional[int] = None
    smart_review_system_prompt: Optional[str] = None

    # Associated LLM by name
    llm_name: Optional[str] = None

    avatar_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ---- Create (response) ----
class BotCreateResponse(BaseModel):
    bot: BotRead
    warning: Optional[str] = None


# ---- Update (can change everything it can) ----
class BotUpdate(BaseModel):
    gitlab_project_path: Optional[str] = None
    gitlab_access_token: Optional[str] = None
    gitlab_webhook_id: Optional[int] = None
    gitlab_webhook_secret: Optional[str] = None
    gitlab_scopes: Optional[List[str]] = None
    gitlab_access_level: Optional[int] = None
    smart_review_system_prompt: Optional[str] = None
    llm_name: Optional[str] = None  # re-point/clear LLM by name
    avatar_name: Optional[str] = None


# ---- Update (response) ----
class BotUpdateResponse(BaseModel):
    bot: BotRead
    warning: Optional[str] = None


# ---- List wrapper ----
class BotReadList(BaseModel):
    total: int
    items: List[BotRead]


class BotActiveResponse(BaseModel):
    active: bool
