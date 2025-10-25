from typing import Optional, List, Any, Dict
from pydantic import BaseModel


# ---- Create ----
class BotCreate(BaseModel):
    gitlab_project_path: str
    gitlab_access_token_id: Optional[int] = None
    gitlab_access_token: Optional[str] = None
    llm_model: str
    llm_context_window: int
    llm_output_tokens: int
    llm_temperature: float
    llm_additional_kwargs: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None


# ---- Read ----
class BotRead(BaseModel):
    id: int
    is_active: bool
    gitlab_project_path: str
    gitlab_access_token_id: Optional[int] = None
    gitlab_webhook_id: Optional[int] = None
    gitlab_webhook_secret: Optional[str] = None
    avatar_url: Optional[str] = None
    llm_model: str
    llm_context_window: int
    llm_output_tokens: int
    llm_temperature: float
    llm_additional_kwargs: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ---- Create (response) ----
class BotCreateResponse(BaseModel):
    bot: BotRead
    warning: Optional[str] = None


# ---- Update (can change everything it can) ----
class BotUpdate(BaseModel):
    is_active: Optional[bool] = None
    gitlab_project_path: Optional[str] = None
    gitlab_access_token_id: Optional[int] = None
    gitlab_access_token: Optional[str] = None
    gitlab_webhook_id: Optional[int] = None
    gitlab_webhook_secret: Optional[str] = None
    avatar_url: Optional[str] = None
    llm_model: Optional[str] = None
    llm_context_window: Optional[int] = None
    llm_output_tokens: Optional[int] = None
    llm_temperature: Optional[float] = None
    llm_additional_kwargs: Optional[Dict[str, Any]] = None


# ---- Update (response) ----
class BotUpdateResponse(BaseModel):
    bot: BotRead
    warning: Optional[str] = None


# ---- List wrapper ----
class BotReadList(BaseModel):
    total: int
    items: List[BotRead]


class BotStatusResponse(BaseModel):
    exists: bool
    active: bool
    status_message: Optional[str] = None
