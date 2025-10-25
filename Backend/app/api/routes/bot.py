from pathlib import Path
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select, func, and_

from app.api.deps import SessionDep, get_current_user, get_gitlab_accout_token
from app.db.models import Bot
from app.schemas.bot import (
    BotCreate,
    BotRead,
    BotReadList,
    BotUpdate,
    BotStatusResponse,
    BotCreateResponse,
    BotUpdateResponse,
)
from app.db.models import User
from app.core.config import settings
from app.core.log import logger
from app.services.gitlab_service import GitlabService, GitLabAccessLevel

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
)

@router.post("/bots/{project_id}", response_model=BotCreateResponse, status_code=status.HTTP_201_CREATED)
def create_bot(
    project_id: str | int,
    data: BotCreate,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    project = gitlab_service.get_user_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitLab project not found or access denied",
        )

    bot = Bot(
        gitlab_project_path=project.path_with_namespace,
        **data.model_dump()
    )
    session.add(bot)
    session.commit()
    session.refresh(bot)
    return BotCreateResponse(bot=BotRead.model_validate(bot))


@router.get("/bots/{project_id}", response_model=BotRead)
def get_bot(
    project_id: str | int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    project = gitlab_service.get_user_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitLab project not found or access denied",
        )

    bot = (
        session.execute(
            select(Bot).where(Bot.gitlab_project_path == project.path_with_namespace)
        )
        .scalars()
        .first()
    )

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found for this project",
        )

    return BotRead.model_validate(bot)


@router.get("/bots/{project_id}/status", response_model=BotStatusResponse)
def get_bot_status(
    project_id: str | int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    project = gitlab_service.get_user_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitLab project not found or access denied",
        )

    bot = (
        session.execute(
            select(Bot)
            .where(Bot.gitlab_project_path == project.path_with_namespace)
            .limit(1)
        )
        .scalars()
        .first()
    )

    if not bot:
        return BotStatusResponse(exists=False, active=False)

    return BotStatusResponse(
        exists=True, active=bot.is_active, status_message=bot.status_message
    )


@router.patch("/bots/{project_id}", response_model=BotRead)
def update_bot(
    project_id: str | int,
    data: BotUpdate,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    project = gitlab_service.get_user_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitLab project not found or access denied",
        )

    bot = (
        session.execute(
            select(Bot).where(Bot.gitlab_project_path == project.path_with_namespace)
        )
        .scalars()
        .first()
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bot, key, value)

    session.add(bot)
    session.commit()
    session.refresh(bot)
    return BotRead.model_validate(bot)
