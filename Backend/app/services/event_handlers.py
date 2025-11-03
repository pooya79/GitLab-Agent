from app.core.log import logger
from typing import Any, Dict

from app.db.models import Bot
from app.db.database import AsyncSession
from app.agents.smart_agent import SmartAgent


async def handle_merge_request_event(bot: Bot, payload: Dict[str, Any], db_session: AsyncSession) -> None:
    """
    Handle a merge request event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling merge request event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    return


async def handle_note_event(bot: Bot, payload: Dict[str, Any], db_session: AsyncSession) -> None:
    """
    Handle a note event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling note event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    return
