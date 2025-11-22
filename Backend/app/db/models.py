"""Lightweight data models used by the MongoDB layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import datetime as dt
from typing import Any, Mapping, Type, TypeVar
from bson import ObjectId

from app.prompts.smart_agent import SMART_AGENT_SYSTEM_PROMPT

T = TypeVar("T", bound="MongoModel")


@dataclass
class MongoModel:
    """Base class for MongoDB models with both _id (ObjectId) and numeric id."""

    _id: ObjectId | None = None  # MongoDB primary key
    id: int | None = None  # Your readable numeric ID

    def to_document(self) -> dict[str, Any]:
        data = asdict(self)

        mongo_id = data.pop("_id", None)
        if mongo_id is None:
            data["_id"] = ObjectId()
        else:
            data["_id"] = mongo_id

        return data

    @classmethod
    def from_document(cls: Type[T], doc: Mapping[str, Any] | None) -> T | None:
        if doc is None:
            return None

        data = dict(doc)

        if "_id" in data:
            data["_id"] = data["_id"]  # keep ObjectId
        return cls(**data)


@dataclass
class Bot(MongoModel):
    name: str = ""
    is_active: bool = True
    gitlab_project_path: str = ""
    gitlab_access_token_id: int | None = None
    gitlab_access_token: str | None = None
    gitlab_user_id: int | None = None
    gitlab_user_name: str | None = None
    gitlab_webhook_id: int | None = None
    gitlab_webhook_secret: str | None = None
    gitlab_webhook_url: str | None = None
    avatar_name: str | None = None
    avatar_url: str | None = None
    llm_model: str = ""
    llm_max_output_tokens: int = 0
    llm_temperature: float = 0.0
    llm_system_prompt: str = SMART_AGENT_SYSTEM_PROMPT
    llm_additional_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class History(MongoModel):
    botname: str = ""
    mr_id: int = 0
    mr_title: str = ""
    gitlab_project_path: str = ""
    username: str | None = None
    messages: str = ""
    request_type: str = ""
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    input_price: float | None = None
    output_price: float | None = None
    total_price: float | None = None
    status: str = "pending"
    error_message: str | None = None
    created_at: dt.datetime = field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )


@dataclass
class OAuthAccount(MongoModel):
    user_id: int | None = None
    provider: str = ""
    provider_account_id: str = ""
    access_token: str = ""
    refresh_token: str | None = None
    token_type: str | None = None
    scope: str | None = None
    expires_at: dt.datetime | None = None
    profile_json: dict[str, Any] | None = None
    last_refreshed_at: dt.datetime | None = None


@dataclass
class RefreshSession(MongoModel):
    user_id: int | None = None
    jti: str = ""
    refresh_token_hash: str = ""
    expires_at: dt.datetime | None = None


@dataclass
class Users(MongoModel):
    email: str = ""
    username: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    is_superuser: bool = False


@dataclass
class CacheEntry:
    key: str
    value: str
    expires_at: dt.datetime | None = None

    def to_document(self) -> dict[str, Any]:
        doc = {
            "_id": self.key,
            "key": self.key,
            "value": self.value,
        }
        if self.expires_at:
            doc["expires_at"] = self.expires_at
        return doc
