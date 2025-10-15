from core.log import logger
import httpx

from llama_index.core.llms import ChatMessage
from sqlalchemy.inspection import inspect

from models.bot import Bot
from clients.gitlab import GitlabClient
from agents.review_agent.smart_review_agent import SmartReviewAgentFactory
from agents.review_agent.prompts import (
    SMART_REVIEW_AGENT_PROMPT,
    SMART_REVIEW_AGENT_USER_PROMPT,
)
from core.config import settings


async def _get_chat_history(
    bot: Bot,
    project_id: int,
    merge_request_iid: int,
    discussion_id: str,
    gitlab_client: GitlabClient,
):
    # Fetch discussion notes
    discussion = await gitlab_client.merge_requests.get_discussion(
        project_id, merge_request_iid, discussion_id
    )
    notes = discussion["notes"]

    max_chat_history = settings.max_chat_history
    chat_history = []
    bot_name = bot.gitlab_access_token_name

    for note in reversed(notes):
        if len(chat_history) > max_chat_history:
            break

        body = note["body"]
        if body.startswith(f"@{bot_name}") and not body.startswith(f"@{bot_name}-cli"):
            chat_history.append(
                ChatMessage(role="user", content=body[len(f"@{bot_name}") :])
            )
        elif note["author"]["username"].startswith(f"project_{project_id}_bot_"):
            chat_history.append(ChatMessage(role="assistant", content=body))

    chat_history.reverse()
    return [] if len(chat_history) == 1 else chat_history[:-1]


async def smart_review(
    user_msg: str,
    bot: Bot,
    event_payload: dict[str, any],
):
    bot_name = bot.gitlab_access_token_name

    if event_payload["object_kind"] == "note":
        project_id = event_payload["project_id"]
        mr_iid = event_payload["merge_request"]["iid"]
        discussion_id = event_payload["object_attributes"]["discussion_id"]
        source_branch = event_payload["merge_request"]["source_branch"]

        # Instantiate GitLab client
        async with GitlabClient(bot.gitlab_access_token) as gitlab_client:
            # Get the list of changed files/diffs in the MR:
            changes = await gitlab_client.merge_requests.list_changes(
                project_id, mr_iid
            )

            # Build a string of diffs for the user prompt:
            diffs_str = ""
            for file_diff in changes:
                old_path = file_diff["old_path"]
                new_path = file_diff["new_path"]
                patch = file_diff["diff"]
                diffs_str += f"\n=== {old_path} → {new_path} ===\n"
                diffs_str += f"{patch}\n"

            # Get merge request title and description
            mr_title = event_payload["merge_request"].get("title", "")
            mr_desc = event_payload["merge_request"].get("description", "")

            system_prompt = bot.smart_review_system_prompt or SMART_REVIEW_AGENT_PROMPT

            system_prompt += (
                f"\n\nMerge Request Info:\nTitle: {mr_title}\n\nDescription: {mr_desc}"
                f"\n\nDiffs:\n{diffs_str}"
            )

            # Get chat history
            chat_history = await _get_chat_history(
                bot, project_id, mr_iid, discussion_id, gitlab_client
            )

            # Get llm model configs
            llm = bot.llm
            model_configs = {
                c.key: getattr(llm, c.key) for c in inspect(llm).mapper.column_attrs
            }
            model_configs["is_function_calling_model"] = True

            agent = SmartReviewAgentFactory.get_agent(
                project_id,
                mr_iid,
                source_branch,
                gitlab_client,
                model_configs,
                system_prompt,
            )

            response = await agent.run(user_msg=user_msg, chat_history=chat_history)

            reply_body = str(response)

            try:
                post_resp = await gitlab_client.merge_requests.reply_discussion(
                    project_id, mr_iid, discussion_id, body=reply_body
                )
                logger.info(
                    f"Posted reply note {post_resp.get('id')} to MR !{mr_iid} in project {bot.gitlab_project_path}"
                )
            except httpx.HTTPStatusError as e:
                # non-2xx response
                status = e.response.status_code
                text = e.response.text
                logger.error(
                    f"Failed to post reply to MR !{mr_iid}: HTTP {status} – {text}"
                )
            except httpx.RequestError as e:
                # network/transport error
                logger.error(f"Network error posting MR reply: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error posting MR reply: {e}")

    elif event_payload["object_kind"] == "merge_request":
        project_id = event_payload["project"]["id"]
        mr_iid = event_payload["object_attributes"]["iid"]
        source_branch = event_payload["object_attributes"]["source_branch"]

        # Instantiate GitLab client
        async with GitlabClient(bot.gitlab_access_token) as gitlab_client:
            # Get the list of changed files/diffs in the MR:
            changes = await gitlab_client.merge_requests.list_changes(
                project_id, mr_iid
            )

            # Build a string of diffs for the user prompt:
            diffs_str = ""
            for file_diff in changes:
                old_path = file_diff["old_path"]
                new_path = file_diff["new_path"]
                patch = file_diff["diff"]
                diffs_str += f"\n=== {old_path} → {new_path} ===\n"
                diffs_str += f"{patch}\n"

            # Get merge request title and description
            mr_title = event_payload["object_attributes"].get("title", "")
            mr_desc = event_payload["object_attributes"].get("description", "")

            system_prompt = bot.smart_review_system_prompt or SMART_REVIEW_AGENT_PROMPT

            system_prompt += (
                f"\n\nMerge Request Info:\nTitle: {mr_title}\n\nDescription: {mr_desc}"
                f"\n\nDiffs:\n{diffs_str}"
            )

            agent = SmartReviewAgentFactory.get_agent(
                project_id, mr_iid, source_branch, gitlab_client, system_prompt
            )

            response = await agent.run(user_msg=SMART_REVIEW_AGENT_USER_PROMPT)

            comment_body = (
                f"Comment from @{bot_name} after reviewing code:\n\n{str(response)}"
            )

            try:
                post_resp = await gitlab_client.merge_requests.create_note(
                    project_id, mr_iid, comment_body
                )
                logger.info(
                    f"Posted comment {post_resp.get('id')} to MR !{mr_iid} in project {bot.gitlab_project_path}"
                )
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                text = e.response.text
                logger.error(
                    f"Failed to post comment to MR !{mr_iid}: HTTP {status} – {text}"
                )
            except httpx.RequestError as e:
                logger.error(f"Network error posting MR comment: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error posting MR comment: {e}")
