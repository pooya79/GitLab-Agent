from typing import Any, Dict

import gitlab
from pydantic_ai import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

from app.agents.smart_agent import SmartAgent
from app.core.config import settings
from app.core.log import logger
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
        model_name=bot.llm_model,
        temperature=bot.llm_temperature,
        max_tokens=bot.llm_max_output_tokens,
        extra_body=bot.llm_additional_kwargs,
    )

    # Send a note that the bot is working on it
    project = gitlab_client.projects.get(gitlab_project_id, lazy=True)
    mr = project.mergerequests.get(mr_iid, lazy=True)
    wait_note = mr.notes.create({"body": "Analyzing the merge request..."})

    # Run the agent with the extracted information
    try:
        response = await smart_agent.run(
            mr_iid=mr_iid,
            project_id=gitlab_project_id,
            system_prompt=bot.llm_system_prompt,
        )
    except Exception as e:
        logger.exception(
            f"Error processing merge request {mr_iid} in project {gitlab_project_id}"
        )
        response = f"Error processing the merge request: {str(e)}"
    finally:
        # Remove the "Analyzing the merge request..." note
        wait_note.delete()

    # Create note as response
    project = gitlab_client.projects.get(gitlab_project_id, lazy=True)
    mr = project.mergerequests.get(mr_iid, lazy=True)
    mr.notes.create({"body": response})


async def handle_note_event(bot: Bot, payload: Dict[str, Any]) -> None:
    """
    Handle a note event from GitLab.

    :param bot: The Bot instance associated with this webhook.
    :param payload: The JSON payload sent by GitLab.
    """
    logger.info(
        f"Handling note event for bot {bot.id} (project {bot.gitlab_project_path})"
    )

    # Extract the note attributes
    attrs = payload.get("object_attributes", {})
    noteable_type = attrs.get("noteable_type")

    # Only reply to merge request notes
    if noteable_type != "MergeRequest":
        logger.info("Note is not on a merge request. No action taken.")
        return

    # Prepare reply details
    project_id = payload.get("project", {}).get("id")
    mr_iid = payload.get("merge_request", {}).get("iid")
    discussion_id = attrs.get("discussion_id")
    note_content = attrs.get("note", "")

    # Check if bot name is mentioned in the note
    if (
        f"@{bot.name.lower()}" not in note_content.lower()
        and f"@{bot.gitlab_user_name}" not in note_content.lower()
    ):
        logger.info("Bot not mentioned in the note. No action taken.")
        return

    # Create a gitlab client
    gitlab_client = gitlab.Gitlab(
        settings.gitlab.base,
        private_token=bot.gitlab_access_token,
    )

    # Gather history of the discussion
    project = gitlab_client.projects.get(project_id, lazy=True)
    mr = project.mergerequests.get(mr_iid, lazy=True)
    discussion = mr.discussions.get(discussion_id)
    notes = discussion.attributes.get("notes", [])
    history = []
    for note in reversed(notes):
        if len(history) > settings.max_chat_history:
            break

        if (
            f"@{bot.name.lower()}" in note.get("body", "").lower()
            or f"@{bot.gitlab_user_name}" in note.get("body", "").lower()
        ):
            history.append(
                ModelRequest(parts=[UserPromptPart(content=note.get("body", ""))])
            )
        else:
            history.append(
                ModelResponse(parts=[TextPart(content=note.get("body", ""))])
            )
    # remove last one
    if history:
        history.pop(0)

    # Create an instance of the SmartAgent
    smart_agent = SmartAgent(
        openrouter_api_key=settings.openrouter_api_key,
        gitlab_client=gitlab_client,
        model_name=bot.llm_model,
        temperature=bot.llm_temperature,
        max_tokens=bot.llm_max_output_tokens,
        extra_body=bot.llm_additional_kwargs,
    )

    # Send a reply that bot is working on it
    wait_note = discussion.notes.create({"body": "Processing your request..."})

    # Run the agent to generate a reply
    try:
        reply = await smart_agent.run(
            user_prompt=note_content,
            mr_iid=mr_iid,
            project_id=project_id,
            system_prompt=bot.llm_system_prompt,
            message_history=history,
        )
    except Exception as e:
        logger.exception(
            f"Error generating reply for note event on MR {mr_iid} in project {project_id}"
        )
        reply = f"Error processing your request: {str(e)}"
    finally:
        # Remove the "Processing your request..." note
        wait_note.delete()

    # Post the reply as a note in the discussion remove previous processing note
    discussion.notes.create({"body": reply})
