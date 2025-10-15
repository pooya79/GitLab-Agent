from pydantic import BaseModel, Field
from fastapi import Query
from typing import Optional, Any, List


class OpenRouterModelsQuery(BaseModel):
    query: Optional[str] = Query(
        None,
        title="Search query",
        description="Filter models by substring match in id or name (case‑insensitive)",
    )


# ---------- Base ----------
class LlmBase(BaseModel):
    name: str
    model: str
    context_window: int
    max_tokens: int
    temperature: float
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)


# ---------- Create ----------
class LlmCreate(LlmBase):
    """Payload for creating an LLM config."""

    pass


# ---------- Update (partial) ----------
class LlmUpdate(BaseModel):
    """Payload for partially updating an LLM config."""

    name: Optional[str] = None
    model: Optional[str] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    additional_kwargs: Optional[dict[str, Any]] = None


# ---------- Read / Response ----------
class LlmRead(BaseModel):
    id: int
    name: str
    model: str
    context_window: int
    max_tokens: int
    temperature: float
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)

    # Pydantic v2: enable ORM mode
    model_config = {"from_attributes": True}


# ---------- List wrapper (optional, handy for index endpoints) ----------
class LlmList(BaseModel):
    total: int
    items: List[LlmRead]