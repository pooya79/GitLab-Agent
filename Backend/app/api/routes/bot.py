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
    BotDeleteResponse,
    BotStatusToggleResponse,
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

    # Check if bot access token is valid
    if bot.gitlab_access_token_id is None:
        return BotStatusResponse(
            status="ERROR",
            error_message="Bot's GitLab access token is not set.",
        )

    gitlab_service = GitlabService(oauth_token=bot.gitlab_access_token)
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
        if (
            project_access_token.expires_at
            and dt.datetime.fromisoformat(project_access_token.expires_at) < NOW()
        ):
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
            error_message="Could not get bot's GitLab access token information (Check if gitlab is connected or access token is working, maybe create a new one).",
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

    # Create project access token for the bot
    try:
        access_token_name = f"{data.name}"
        project_token = gitlab_service.create_project_token(
            project.id,
            access_token_name,
            scopes=["api"],
            expires_at=None,
        )
    except Exception as e:
        logger.error(f"Error creating project access token for bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project access token for the bot. Check your connection with GitLab.",
        )

    # Get username associated with the token
    try:
        new_gitlab_service = GitlabService(oauth_token=project_token.token)
        user_info = new_gitlab_service.get_user_info()
        if not user_info:
            raise Exception("Could not fetch user info with the created token.")
        project_token.user_name = user_info.username
    except Exception as e:
        # Revoke the created project token in case of failure
        try:
            gitlab_service.revoke_project_token(project.id, project_token.id)
        except Exception as revoke_error:
            logger.error(
                f"Error revoking project token after user info fetch failure: {revoke_error}"
            )

        logger.error(f"Error fetching user info for bot token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user info for the bot's access token. Check your connection with GitLab.",
        )

    # Create project webhook for the bot
    try:
        webhook_url = f"{settings.backend_url}/api/v1/webhooks/{project_token.user_id}"
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
        # Revoke the created project token in case of webhook creation failure
        try:
            gitlab_service.revoke_project_token(project.id, project_token.id)
        except Exception as revoke_error:
            logger.error(
                f"Error revoking project token after webhook creation failure: {revoke_error}"
            )

        logger.error(f"Error creating project webhook for bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project webhook for the bot. Check your connection with GitLab.",
        )

    bot = Bot(
        name=data.name,
        gitlab_access_token_id=project_token.id,
        gitlab_access_token=project_token.token,
        gitlab_user_id=project_token.user_id,
        gitlab_user_name=project_token.user_name,
        gitlab_project_path=project.path_with_namespace,
        gitlab_webhook_id=webhook.id,
        gitlab_webhook_secret=webhook_secret_token,
        gitlab_webhook_url=webhook_url,
        llm_model=settings.llm_model,
        llm_max_output_tokens=settings.llm_max_output_tokens,
        llm_temperature=settings.llm_temperature,
        avatar_url=f"{settings.backend_url}/{settings.avatar_default_url}",
    )
    try:
        session.add(bot)
        await session.commit()
        await session.refresh(bot)
    except Exception as e:
        # Clean up created GitLab resources in case of DB failure
        try:
            gitlab_service.delete_webhook(project.id, webhook.id)
        except Exception as webhook_error:
            logger.error(
                f"Error deleting webhook after bot DB creation failure: {webhook_error}"
            )
        try:
            gitlab_service.revoke_project_token(project.id, project_token.id)
        except Exception as token_error:
            logger.error(
                f"Error revoking project token after bot DB creation failure: {token_error}"
            )

        logger.error(f"Error saving bot to database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save bot to the database.",
        )
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


@router.delete("/{bot_id}", response_model=BotDeleteResponse)
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
    warning_message = ""
    # Clean up GitLab resources
    try:
        if bot.gitlab_webhook_id:
            gitlab_service.delete_webhook(
                bot.gitlab_project_path, bot.gitlab_webhook_id
            )
    except Exception as e:
        logger.error(f"Error deleting webhook for bot {bot_id}: {e}")
        warning_message += f"Failed to delete GitLab webhook for bot {bot.name}."

    try:
        if bot.gitlab_access_token_id:
            gitlab_service.revoke_project_token(
                bot.gitlab_project_path, bot.gitlab_access_token_id
            )
    except Exception as e:
        logger.error(f"Error deleting project token for bot {bot_id}: {e}")
        if warning_message:
            warning_message += "\n"
        warning_message += f"Failed to revoke GitLab project token for bot {bot.name}."

    await session.delete(bot)
    await session.commit()
    if not warning_message:
        return BotDeleteResponse()
    return BotDeleteResponse(warning=warning_message)


@router.patch("/{bot_id}/new-access-token", response_model=BotUpdateResponse)
async def create_new_bot_access_token(
    bot_id: int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Create a new access token for a bot by its ID and revoke the old one.
    """
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )
    old_token_id = bot.gitlab_access_token_id

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    # Create new project access token
    try:
        project_token = gitlab_service.create_project_token(
            bot.gitlab_project_path,
            bot.name,
            scopes=["api"],
        )
    except Exception as e:
        logger.error(f"Error creating project token for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project token for the bot. Check your connection with GitLab.",
        )

    # Fetch username associated with the new token
    try:
        new_gitlab_service = GitlabService(oauth_token=project_token.token)
        user_info = new_gitlab_service.get_user_info()
        if not user_info:
            raise Exception("Could not fetch user info with the created token.")
        project_token.user_name = user_info.username
    except Exception as e:
        # Revoke the created project token in case of failure
        try:
            gitlab_service.revoke_project_token(
                bot.gitlab_project_path, project_token.id
            )
        except Exception as revoke_error:
            logger.error(
                f"Error revoking project token after user info fetch failure: {revoke_error}"
            )

        logger.error(f"Error fetching user info for new bot token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user info for the new bot's access token. Check your connection with GitLab.",
        )

    # Revoke old token and update bot with new token info
    try:
        old_token = gitlab_service.get_project_token(
            bot.gitlab_project_path, old_token_id
        )
        if old_token_id and old_token and old_token.revoked is False:
            gitlab_service.revoke_project_token(bot.gitlab_project_path, old_token_id)

        bot.gitlab_access_token_id = project_token.id
        bot.gitlab_access_token = project_token.token
        bot.gitlab_user_id = project_token.user_id
        bot.gitlab_user_name = project_token.user_name
        session.add(bot)
        await session.commit()
        await session.refresh(bot)
    except Exception as e:
        logger.error(f"Error updating bot with new token for bot {bot_id}: {e}")
        # Revoke the created project token in case of DB update failure
        try:
            gitlab_service.revoke_project_token(
                bot.gitlab_project_path, project_token.id
            )
        except Exception as revoke_error:
            logger.error(
                f"Error revoking project token after bot DB update failure: {revoke_error}"
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot with new access token.",
        )

    return BotUpdateResponse(bot=BotRead.model_validate(bot))


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


@router.patch("/{bot_id}/toggle-active", response_model=BotStatusToggleResponse)
async def toggle_bot_active(
    bot_id: int,
    session: SessionDep,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Toggle a bot's active status by its ID.
    """
    result = await session.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalars().first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found"
        )

    bot.is_active = not bot.is_active
    session.add(bot)
    await session.commit()
    await session.refresh(bot)
    return BotStatusToggleResponse(is_active=bot.is_active)


@router.delete("/{bot_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
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
