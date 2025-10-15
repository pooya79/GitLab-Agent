from typing import Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, ForeignKey, JSON, String
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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
