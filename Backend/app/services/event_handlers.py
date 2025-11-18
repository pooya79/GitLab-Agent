from typing import Any, Dict
import gitlab

from app.db.models import Bot
from app.db.database import AsyncSession
from app.agents.smart_agent import SmartAgent
from app.core.log import logger
from app.core.config import settings


async def handle_merge_request_event(
    bot: Bot, payload: Dict[str, Any], db_session: AsyncSession
) -> None:
    """
    Handle a merge request event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling merge request event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    trigger = False
    action = payload["object_attributes"]["action"]

    changes = payload.get("changes", {})
    # Trigger only when bot is newly added as reviewer
    if changes:
        reviewers_change = changes.get("reviewers")
        if reviewers_change:
            previous_reviewers = {
                reviewer["id"] for reviewer in reviewers_change.get("previous", [])
            }
            current_reviewers = {
                reviewer["id"] for reviewer in reviewers_change.get("current", [])
            }
            if (
                bot.gitlab_user_id in current_reviewers
                and bot.gitlab_user_id not in previous_reviewers
            ):
                trigger = True

    # Trigger if Re-request review is made
    if action == "update" and changes:
        reviewers = changes.get("reviewers")
        if reviewers and isinstance(reviewers, list):
            for reviewer in reviewers:
                if (
                    reviewer.get("id") == bot.gitlab_user_id
                    and reviewer.get("re_requested", False) is True
                ):
                    trigger = True
                    break

    if not trigger:
        logger.info("No action required for this merge request event.")
        return

    # Extract relevant information from the payload
    mr_iid = payload.get("object_attributes", {}).get("iid")
    gitlab_project_id = payload.get("project", {}).get("id")

    # Create GitLab client
    gitlab_client = gitlab.Gitlab(
        settings.gitlab.base,
        private_token=bot.gitlab_access_token,
    )

    # Create an instance of the SmartAgent
    smart_agent = SmartAgent(
        openrouter_api_key=settings.openrouter_api_key,
        gitlab_client=gitlab_client,
        db_session=db_session,
        model_name=bot.llm_model,
        temperature=bot.llm_temperature,
        max_tokens=bot.llm_max_output_tokens,
        extra_body=bot.llm_additional_kwargs,
    )

    # Run the agent with the extracted information
    await smart_agent.run(
        mr_iid=mr_iid,
        project_id=gitlab_project_id,
        system_prompt=bot.llm_system_prompt,
    )

    return


async def handle_note_event(
    bot: Bot, payload: Dict[str, Any], db_session: AsyncSession
) -> None:
    """
    Handle a note event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling note event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    return
