from pathlib import Path
import logging
import uuid
import httpx
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select, func, and_

from app.api.deps import SessionDep, get_current_user
from app.db.models import Bot, Llm
from app.schemas.bot import (
    BotCreate,
    BotRead,
    BotReadList,
    BotUpdate,
    BotActiveResponse,
    BotCreateResponse,
    BotUpdateResponse,
)
from clients.gitlab import (
    GitlabClient,
    GitLabAccessLevel,
)
from app.db.models import User
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
)


async def validate_gitlab_access(
    gitlab_project_path: str,
    client: GitlabClient,
    min_access_level: int = GitLabAccessLevel.REPORTER,
) -> int:
    """
    Throws an HTTPException if:
      - the token is invalid (404)
      - the project doesn't exist / is inaccessible (403/404)
      - the token lacks Developer or Maintainer rights

    Returns:
        - int: access level of token
    """
    try:
        project = await client.projects.get(gitlab_project_path)
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 401:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitLab API token.",
            )
        elif code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token not permitted to access project '{gitlab_project_path}'.",
            )
        elif code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{gitlab_project_path}' not found.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unexpected GitLab response (HTTP {code}).",
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error communicating with GitLab: {e}",
        )

    access = project["permissions"].get("project_access")
    if not access or access["access_level"] < min_access_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"API token access level is too low (required ≥ {min_access_level})."
            ),
        )

    return access["access_level"]


async def _resolve_llm_id_from_name(
    session: SessionDep, llm_name: Optional[str]
) -> Optional[int]:
    """Return Llm.id for a given name; if llm_name is None return None; if not found → 404."""
    if llm_name is None:
        return None
    res = await session.execute(select(Llm.id).where(Llm.name == llm_name))
    llm_id = res.scalar_one_or_none()
    if llm_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM with name '{llm_name}' not found.",
        )
    return llm_id


def _bot_to_read(bot: Bot) -> BotRead:
    """Map ORM Bot -> BotRead, exposing llm_name and avatar_name."""
    return BotRead(
        id=bot.id,
        gitlab_project_path=bot.gitlab_project_path,
        gitlab_access_token=bot.gitlab_access_token,
        gitlab_access_token_name=bot.gitlab_access_token_name,
        gitlab_webhook_id=bot.gitlab_webhook_id,
        gitlab_webhook_secret=bot.gitlab_webhook_secret,
        gitlab_scopes=bot.gitlab_scopes or [],
        gitlab_access_level=bot.gitlab_access_level,
        smart_review_system_prompt=bot.smart_review_system_prompt,
        llm_name=(bot.llm.name if getattr(bot, "llm", None) else None),
        avatar_name=getattr(bot, "avatar_name", None),
    )


def _avatar_path(avatar_name: str) -> Path:
    """Resolve an avatar filename to disk. Adjust if your dir differs."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    # Expect avatars under: app/assets/avatars/<file>
    path = base_dir / "assets" / "avatars" / avatar_name
    return path


@router.post("/", response_model=BotCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_in: BotCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> BotCreateResponse:
    # unique per user
    result = await session.execute(
        select(Bot).where(
            and_(
                Bot.gitlab_project_path == bot_in.gitlab_project_path,
            )
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Bot for project '{bot_in.gitlab_project_path}' already exists.",
        )

    llm_id = await _resolve_llm_id_from_name(session, bot_in.llm_name)
    warning: Optional[str] = None

    async with GitlabClient(token=bot_in.gitlab_access_token) as client:
        access_level = await validate_gitlab_access(
            gitlab_project_path=bot_in.gitlab_project_path,
            client=client,
            min_access_level=GitLabAccessLevel.MAINTAINER,
        )

        # Fetch token details (name + scopes)
        try:
            token_details = await client.tokens.get(bot_in.gitlab_project_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not fetch GitLab token details: {e}",
            )

        token_name = token_details.get("name")
        scopes = token_details.get("scopes") or []

        # persist
        bot = Bot(
            gitlab_project_path=bot_in.gitlab_project_path,
            gitlab_access_token=bot_in.gitlab_access_token,
            gitlab_access_token_name=token_name,
            gitlab_scopes=scopes,
            gitlab_access_level=access_level,
            llm_id=llm_id,
            avatar_name="default.png",
        )
        session.add(bot)
        await session.commit()
        await session.refresh(bot)

        # Create webhook
        hook_url = f"{settings.host_url}/api/v{settings.api_version}/webhooks/{bot.id}"
        secret = uuid.uuid4().hex
        try:
            hook = await client.projects.create_webhook(
                project_id=bot.gitlab_project_path,
                hook_url=hook_url,
                enable_ssl_verification=False,
                token=secret,
            )
        except httpx.HTTPStatusError as e:
            await session.delete(bot)
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create GitLab webhook: HTTP {e.response.status_code}",
            )
        except httpx.RequestError as e:
            await session.delete(bot)
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create GitLab webhook: {e}",
            )

        # Try setting default avatar
        try:
            image_path = _avatar_path(bot.avatar_name or "default.png")
            await client.users.update_avatar(image_path)
        except Exception as e:
            warning = f"Could not set bot avatar: {e}"
            logger.error(warning)

    # store webhook info
    bot.gitlab_webhook_id = hook["id"]
    bot.gitlab_webhook_secret = secret
    session.add(bot)
    await session.commit()
    await session.refresh(bot)

    return BotCreateResponse(bot=_bot_to_read(bot), warning=warning)


@router.get(
    "/",
    response_model=BotReadList,
)
async def list_bots(
    session: SessionDep,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
) -> BotReadList:
    """
    Retrieve a paginated list of bots along with total count.
    """
    base = select(Bot)
    count_stmt = select(func.count(Bot.id))

    total = (await session.execute(count_stmt)).scalar_one()
    bots = (await session.execute(base.offset(skip).limit(limit))).scalars().all()
    return BotReadList(total=total, items=[_bot_to_read(b) for b in bots])


@router.get(
    "/{bot_id}",
    response_model=BotRead,
)
async def get_bot(
    bot_id: int, session: SessionDep, current_user: User = Depends(get_current_user)
) -> BotRead:
    """
    Get details of a single bot by its ID.
    """
    bot = await session.get(Bot, bot_id)
    if not bot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Bot {bot_id} not found.")
    return _bot_to_read(bot)


@router.patch(
    "/{bot_id}",
    response_model=BotUpdateResponse,
)
async def update_bot(
    bot_id: int,
    bot_update: BotUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> BotUpdateResponse:
    """
    Update an existing bot's data.
    """
    bot = await session.get(Bot, bot_id)
    if not bot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Bot {bot_id} not found.")

    updates = bot_update.model_dump(exclude_unset=True)

    # If changing project path, ensure uniqueness
    new_path = updates.get("gitlab_project_path")
    if new_path and new_path != bot.gitlab_project_path:
        dup = await session.execute(
            select(Bot).where(
                and_(
                    Bot.gitlab_project_path == new_path,
                    Bot.id != bot.id,
                )
            )
        )
        if dup.scalars().first():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Bot for project '{new_path}' already exists.",
            )

    # Resolve LLM by name if provided
    if "llm_name" in updates:
        llm_name = updates.pop("llm_name")
        bot.llm_id = await _resolve_llm_id_from_name(session, llm_name)

    warning: Optional[str] = None

    # Apply other fields
    for field, value in updates.items():
        setattr(bot, field, value)

    async with GitlabClient(token=bot.gitlab_access_token) as client:
        # If they changed the access token, re-validate access & refresh scopes
        if "gitlab_access_token" in bot_update.model_fields_set:
            access_level = await validate_gitlab_access(
                gitlab_project_path=bot.gitlab_project_path,
                client=client,
            )
            bot.gitlab_access_level = access_level
            try:
                token_details = await client.tokens.get(bot.gitlab_project_path)
                bot.gitlab_access_token_name = token_details.get("name")
                bot.gitlab_scopes = token_details.get("scopes") or []
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Could not retrieve GitLab token scopes: {e}",
                )

        # If an avatar_name is part of this update, try updating GitLab avatar too
        if "avatar_name" in updates:
            try:
                image_path = _avatar_path(bot.avatar_name or "default.png")
                await client.users.update_avatar(image_path)
            except Exception as e:
                warning = f"Could not update bot avatar: {e}"
                logger.error(warning)

    await session.commit()
    await session.refresh(bot)
    return BotUpdateResponse(bot=_bot_to_read(bot), warning=warning)


@router.delete(
    "/{bot_id}",
)
async def delete_bot(
    bot_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a bot by its ID, and also remove its GitLab webhook if present.
    If we lack permission to delete the hook, we still delete the bot but return a warning.
    """
    bot = await session.get(Bot, bot_id)
    if not bot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Bot {bot_id} not found.")

    warning: Optional[str] = None

    # Remove webhook if we have one recorded
    if bot.gitlab_webhook_id:
        async with GitlabClient(token=bot.gitlab_access_token) as client:
            try:
                await client.projects.delete_webhook(
                    bot.gitlab_project_path, hook_id=bot.gitlab_webhook_id
                )
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                if code in (401, 403):
                    warning = "Bot deleted, but webhook was not removed: insufficient permissions."
                else:
                    warning = (
                        f"Bot deleted, but failed to remove webhook (HTTP {code})."
                    )
            except httpx.RequestError as e:
                warning = f"Bot deleted, but error removing webhook: {e}"

    # Delete the bot record
    await session.delete(bot)
    await session.commit()

    if warning:
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"warning": warning}
        )
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{bot_id}/is_active",
    response_model=BotActiveResponse,
    status_code=status.HTTP_200_OK,
)
async def is_bot_active(
    bot_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
    """
    Check if a bot’s GitLab token is active
    """
    bot = await session.get(Bot, bot_id)
    if not bot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Bot {bot_id} not found.")

    async with GitlabClient(bot.gitlab_access_token) as client:
        try:
            token_details = await client.tokens.get(bot.gitlab_project_path)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ):
                return {"active": False}
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error fetching token details: {e}",
            )

    active = token_details.get("active")
    if active is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Malformed response from GitLab",
        )
    return {"active": active}
