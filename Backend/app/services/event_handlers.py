from app.core.log import logger
from typing import Any, Dict

from app.db.models import Bot


async def handle_merge_request_event(bot: Bot, payload: Dict[str, Any]) -> None:
    """
    Handle a merge request event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling merge request event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    return

    # changes = payload.get("changes")

    # if changes:
    #     reviewers = changes.get("reviewers")
    #     if reviewers:
    #         previous_reviewers_names = [r["name"] for r in reviewers.get("previous")]
    #         current_reviewers_names = [r["name"] for r in reviewers.get("current")]

    #         token_name = bot.gitlab_access_token_name

    #         if (
    #             token_name in current_reviewers_names
    #             and token_name not in previous_reviewers_names
    #         ):
    #             logger.info(
    #                 "Starting smart review for bot {bot.id} (project {bot.gitlab_project_path})"
    #             )
    #             await smart_review(user_msg=None, bot=bot, event_payload=payload)


async def handle_note_event(bot: Bot, payload: Dict[str, Any]) -> None:
    """
    Handle a note event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling note event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    return

    # # Extract the note attributes
    # attrs = payload.get("object_attributes", {})
    # noteable_type = attrs.get("noteable_type")

    # # Only reply to merge request comments
    # if noteable_type != "MergeRequest":
    #     logger.info(f"Ignoring note event for type: {noteable_type}")
    #     return

    # # Prepare reply details
    # project_id = payload.get("project_id")
    # user_name = payload.get("user", {}).get("username")
    # original_note = attrs.get("note")

    # if user_name.startswith(f"project_{project_id}_bot_"):
    #     logger.info(f"Ignoring bot-generated comment by {user_name}")
    #     return

    # mention_command = f"@{bot.gitlab_access_token_name}/"
    # mention_smart = f"@{bot.gitlab_access_token_name}"

    # if original_note.startswith(mention_command):
    #     full_command = original_note[len(mention_command) :]
    #     logger.info(f"Running command: {full_command}")
    #     try:
    #         await command_handler(full_command, bot, payload)
    #     except Exception as e:
    #         logger.error(f"Error: {e}")
    # elif original_note.startswith(mention_smart):
    #     # remove the mention_smart prefix and any leading spacess
    #     note_body = original_note[len(mention_smart) :].lstrip()
    #     logger.info(f"Smart review with prompt: {note_body}")
    #     try:
    #         await smart_review(note_body, bot, payload)
    #     except Exception as e:
    #         logger.error(f"Error: {e}")
