import uuid
import datetime as dt

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response
from sqlalchemy import select, func, and_

from app.api.deps import SessionDep, get_gitlab_accout_token
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
from app.core.config import settings
from app.core.log import logger
from app.services.gitlab_service import GitlabService, GitLabAccessLevel
from app.services.cache_service import NOW

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
)

AVAILABLE_BOT_AVATARS = {
    avatar_name: f"{settings.backend_url}/api/static/avatars/{avatar_name}"
    for avatar_name in [
        "8-bit_bot",
        "analyst",
        "cyber_samurai",
        "default",
        "galactic_bot",
        "hacker",
        "khosro",
        "librarian",
        "steampunk",
    ]
}


@router.get("/{bot_id}/status", response_model=BotStatusResponse)
async def get_bot_status(
    bot_id: int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Get the status of a bot by its ID.
    """
    result = await session.execute(select(Bot).where(and_(Bot.id == bot_id)))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )

    if not bot.is_active:
        return BotStatusResponse(status="STOPPED")

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    # Check if bot access token is valid
    if bot.gitlab_access_token_id is None:
        return BotStatusResponse(
            status="ERROR",
            error_message="Bot's GitLab access token is not set.",
        )
    try:
        project_access_token = gitlab_service.get_project_token(
            bot.gitlab_project_path, bot.gitlab_access_token_id
        )

        if not project_access_token:
            return BotStatusResponse(
                status="ERROR",
                error_message="Bot's GitLab project is invalid or has been revoked.",
            )

        # Check if token is revoked
        if project_access_token.revoked:
            return BotStatusResponse(
                status="ERROR",
                error_message=f"Bot's GitLab access token ({project_access_token.name}) has been revoked.",
            )

        # Check its expiry
        if project_access_token.expires_at and dt.datetime.fromisoformat(project_access_token.expires_at) < NOW():
            return BotStatusResponse(
                status="ERROR",
                error_message=f"Bot's GitLab access token ({project_access_token.name}) has expired.",
            )

        # Check its access level
        if project_access_token.access_level < GitLabAccessLevel.MAINTAINER:
            return BotStatusResponse(
                status="ERROR",
                error_message=f"Bot's GitLab access token ({project_access_token.name}) does not have sufficient access level (minimum MAINTAINER).",
            )

        # Check its scope
        required_scopes = {"api"}
        token_scopes = set(project_access_token.scopes)
        if not required_scopes.issubset(token_scopes):
            return BotStatusResponse(
                status="ERROR",
                error_message=f"Bot's GitLab access token ({project_access_token.name}) does not have required scopes: {', '.join(required_scopes)}.",
            )

    except Exception as e:
        logger.error(f"Could not get bot's GitLab access token information: {e}")
        return BotStatusResponse(
            status="ERROR",
            error_message=f"Could not get bot's GitLab access token ({bot.gitlab_access_token_id}) information (Check if gitlab is connected).",
        )

    # Check if bot webhook is valid
    if bot.gitlab_webhook_id is None:
        return BotStatusResponse(
            status="ERROR",
            error_message="Bot's GitLab webhook is not set up.",
        )
    try:
        webhook = gitlab_service.get_webhook(
            bot.gitlab_project_path, bot.gitlab_webhook_id
        )
        if not webhook:
            return BotStatusResponse(
                status="ERROR",
                error_message="Bot's GitLab webhook is invalid or has been removed.",
            )

        # Check its URL
        if webhook.url != bot.gitlab_webhook_url:
            return BotStatusResponse(
                status="ERROR",
                error_message="Bot's GitLab webhook URL is invalid.",
            )

        # Check if required events are enabled
        required_events = {"note_events", "merge_requests_events"}
        for event in required_events:
            if not getattr(webhook, event, False):
                return BotStatusResponse(
                    status="ERROR",
                    error_message=f"Bot's GitLab webhook is missing required event: {event}.",
                )

    except Exception as e:
        logger.error(f"Could not get bot's GitLab webhook information: {e}")
        return BotStatusResponse(
            status="ERROR",
            error_message="Bot's GitLab webhook is invalid or has been removed.",
        )

    return BotStatusResponse(status="ACTIVE")


@router.post("/", response_model=BotCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    data: BotCreate,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Create a new bot for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    project = gitlab_service.get_user_project(data.gitlab_project_path)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitLab project not found or access denied",
        )

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    # Create project webhook for the bot
    try:
        webhook_url = f"{settings.backend_url}/api/v1/webhooks/{data.name}"
        events = {
            "note_events": True,
            "merge_requests_events": True,
        }
        webhook_secret_token = uuid.uuid4().hex
        webhook = gitlab_service.create_webhook(
            project.id,
            webhook_url,
            events,
            enable_ssl_verification=settings.gitlab.webhook_ssl_verify,
            token=webhook_secret_token,
        )
    except Exception as e:
        logger.error(f"Error creating project webhook for bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project webhook for the bot. Check your connection with GitLab.",
        )

    # Create project access token for the bot
    try:
        access_token_name = f"bot-token-{data.name}-{uuid.uuid4().hex[:8]}"
        project_token = gitlab_service.create_project_token(
            project.id,
            access_token_name,
            scopes=["api"],
            expires_at=None,
        )
    except Exception as e:
        logger.error(f"Error creating project access token for bot: {e}")
        # Clean up the created project webhook
        try:
            gitlab_service.delete_webhook(project.id, webhook.id)
        except Exception as cleanup_error:
            logger.error(
                f"Error cleaning up project webhook after token failure: {cleanup_error}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project webhook for the bot. Check your connection with GitLab.",
        )

    bot = Bot(
        name=data.name,
        gitlab_access_token_id=project_token.id,
        gitlab_access_token=project_token.token,
        gitlab_project_path=project.path_with_namespace,
        gitlab_webhook_id=webhook.id,
        gitlab_webhook_secret=webhook_secret_token,
        gitlab_webhook_url=webhook_url,
        llm_model=settings.llm_model,
        llm_context_window=settings.llm_context_window,
        llm_output_tokens=settings.llm_output_tokens,
        llm_temperature=settings.llm_temperature,
        avatar_url=f"{settings.backend_url}/{settings.avatar_default_url}",
    )
    session.add(bot)
    await session.commit()
    await session.refresh(bot)
    return BotCreateResponse(bot=BotRead.model_validate(bot))


@router.get("/", response_model=BotReadList)
async def list_bots(
    session: SessionDep,
    page: int = 1,
    per_page: int = 20,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    List all bots with pagination.
    """
    result = await session.execute(select(func.count(Bot.id)))
    total = result.scalar_one()

    result = await session.execute(
        select(Bot).offset((page - 1) * per_page).limit(per_page)
    )
    bots = result.scalars().all()

    return BotReadList(
        total=total,
        items=[BotRead.model_validate(bot) for bot in bots],
    )


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Delete a bot by its ID.
    """
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    warning_message = None
    # Clean up GitLab resources
    try:
        if bot.gitlab_webhook_id:
            gitlab_service.delete_webhook(
                bot.gitlab_project_path, bot.gitlab_webhook_id
            )
    except Exception as e:
        logger.error(f"Error deleting webhook for bot {bot_id}: {e}")
        warning_message = f"Failed to delete GitLab webhook for bot {bot.name}."

    try:
        if bot.gitlab_access_token_id:
            gitlab_service.revoke_project_token(
                bot.gitlab_project_path, bot.gitlab_access_token_id
            )
    except Exception as e:
        logger.error(f"Error deleting project token for bot {bot_id}: {e}")
        warning_message = f"Failed to revoke GitLab project token for bot {bot.name}."

    await session.delete(bot)
    await session.commit()
    return Response(
        status_code=status.HTTP_204_NO_CONTENT, warning_message=warning_message
    )


@router.patch("/{bot_id}", response_model=BotUpdateResponse)
async def update_bot(
    bot_id: int,
    data: BotUpdate,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Update a bot by its ID.
    """
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bot, key, value)

    session.add(bot)
    await session.commit()
    await session.refresh(bot)
    return BotUpdateResponse(bot=BotRead.model_validate(bot))


@router.delete("/{bod_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_bot_token(
    bot_id: int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Revoke a bot's GitLab project access token.
    """
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    try:
        if bot.gitlab_access_token_id:
            gitlab_service.revoke_project_token(
                bot.gitlab_project_path, bot.gitlab_access_token_id
            )
            bot.gitlab_access_token_id = None
            bot.gitlab_access_token = None
            session.add(bot)
            await session.commit()
            await session.refresh(bot)
    except Exception as e:
        logger.error(f"Error revoking project token for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke GitLab project token for the bot.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{bot_id}/rotate-token", response_model=BotRead)
async def rotate_bot_token(
    bot_id: int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Rotate a bot's GitLab project access token.
    """
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    try:
        if bot.gitlab_access_token_id:
            new_token = gitlab_service.rotate_project_token(
                bot.gitlab_project_path, bot.gitlab_access_token_id
            )
            bot.gitlab_access_token_id = new_token.id
            bot.gitlab_access_token = new_token.token
            session.add(bot)
            await session.commit()
            await session.refresh(bot)
            return BotRead.model_validate(bot)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot does not have an existing GitLab access token to rotate.",
            )
    except Exception as e:
        logger.error(f"Error rotating project token for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate GitLab project token for the bot.",
        )


@router.get("/available-avatars", response_model=dict[str, str])
async def get_available_avatars():
    """
    Get a list of available bot avatars.
    """
    return AVAILABLE_BOT_AVATARS
