from typing import Any, Optional
import datetime as dt
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy import Text, ForeignKey, JSON, String, UniqueConstraint, Index, DateTime
from app.prompts.smart_review_agent import SMART_REVIEW_AGENT_PROMPT

# Base class for models
Base = declarative_base()


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    gitlab_project_path: Mapped[str] = mapped_column(nullable=False)
    gitlab_access_token_id: Mapped[int] = mapped_column(nullable=True)
    gitlab_access_token: Mapped[str] = mapped_column(nullable=True)
    gitlab_webhook_id: Mapped[int] = mapped_column(nullable=True)
    gitlab_webhook_secret: Mapped[str] = mapped_column(nullable=True)

    avatar_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    llm_model: Mapped[str] = mapped_column(nullable=False)
    llm_context_window: Mapped[int] = mapped_column(nullable=False)
    llm_output_tokens: Mapped[int] = mapped_column(nullable=False)
    llm_temperature: Mapped[float] = mapped_column(nullable=False)
    llm_additional_kwargs: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=True
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
        Index("ix_user_provider", "user_id", "provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )

    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[dt.datetime]] = mapped_column(nullable=True)

    profile_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    last_refreshed_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    user: Mapped["Users"] = relationship(
        "Users", back_populates="oauth_accounts", lazy="joined"
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    jti: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    expires_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["Users"] = relationship(
        "Users", back_populates="sessions", lazy="joined"
    )


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(nullable=False, default=False)

    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[RefreshSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Cache(Base):
    __tablename__ = "cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
