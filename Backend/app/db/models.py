from typing import Any, Optional
import datetime as dt
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, ForeignKey, JSON, String, UniqueConstraint, Index, DateTime
from app.db.database import Base
from app.prompts.smart_review_agent import SMART_REVIEW_AGENT_PROMPT


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    gitlab_project_path: Mapped[str] = mapped_column(nullable=False)
    gitlab_access_token: Mapped[str] = mapped_column(nullable=False)
    gitlab_access_token_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    gitlab_webhook_id: Mapped[int] = mapped_column(nullable=True)
    gitlab_webhook_secret: Mapped[str] = mapped_column(nullable=True)
    gitlab_scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    gitlab_access_level: Mapped[int] = mapped_column(nullable=False)

    avatar_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    smart_review_system_prompt: Mapped[str] = mapped_column(
        Text, default=SMART_REVIEW_AGENT_PROMPT, nullable=True
    )

    llm_id: Mapped[int] = mapped_column(
        ForeignKey("llms.id", ondelete="RESTRICT"),  # prevents deleting LLM if in use
        nullable=False,
        index=True,
    )
    llm: Mapped["Llm"] = relationship("Llm", back_populates="bots", lazy="joined")


class Llm(Base):
    __tablename__ = "llms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)

    model: Mapped[str] = mapped_column(nullable=False)

    context_window: Mapped[int] = mapped_column(nullable=False)
    max_tokens: Mapped[int] = mapped_column(nullable=False)
    temperature: Mapped[float] = mapped_column(nullable=False)

    additional_kwargs: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=True
    )

    bots: Mapped[list["Bot"]] = relationship(
        "Bot",
        back_populates="llm",
        lazy="selectin",
        cascade="save-update, merge",
        passive_deletes=True,
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id", name="uq_provider_account"),
        Index("ix_user_provider", "user_id", "provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)

    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
