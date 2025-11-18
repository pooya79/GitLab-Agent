import gitlab
import requests
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from sqlalchemy import select
import json

from app.db.database import AsyncSession
from app.db.models import History
from app.prompts.smart_agent import SMART_AGENT_SYSTEM_PROMPT, SMART_AGENT_USER_PROMPT
from app.agents.utils import token_counter
from app.services.cache_service import NOW
from app.core.config import settings
from app.core.log import logger


# Tools
def tools_wrapper(
    gitlab_client: gitlab.Gitlab, mr_iid: int, project_id: int, source_branch: str
) -> list[callable]:
    """Return the list of tools available to the Smart Agent."""

    def approve_mr() -> str:
        """Tool to approve a GitLab Merge Request."""
        try:
            project = gitlab_client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            mr.approve()
            return "Approved the merge request."
        except gitlab.GitlabError as e:
            logger.error(
                f"Failed to approve merge request {mr_iid} in project {project_id}, Error: {str(e)}"
            )
            return f"Failed to approve the merge request: {str(e)}"

    def unapprove_mr() -> str:
        """Tool to unapprove a GitLab Merge Request. You might get error if you have not approved it yet. Use this tool only one time per conversation."""
        try:
            project = gitlab_client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
            mr.unapprove()
            return "Unapproved the merge request."
        except gitlab.GitlabError as e:
            logger.error(
                f"Failed to unapprove merge request {mr_iid} in project {project_id}, Error: {str(e)}"
            )
            return f"Failed to unapprove the merge request: {str(e)}"

    def get_file(file_path: str) -> str:
        """Tool to get the content of a file in the GitLab repository. given its path. you can use this tool only 2 times per conversation."""
        project = gitlab_client.projects.get(project_id, lazy=True)
        try:
            file = project.files.get(file_path=file_path, ref=source_branch)
            file_content = file.decode().decode("utf-8")
            return file_content
        except gitlab.GitlabError as e:
            logger.error(
                f"Failed to retrieve file {file_path} from project {project_id} at branch {source_branch}, Error: {str(e)}"
            )
            return "Error: " + str(e)

    return [approve_mr, unapprove_mr, get_file]


class SmartAgent:
    def __init__(
        self,
        openrouter_api_key: str,
        gitlab_client: gitlab.Gitlab,
        db_session: AsyncSession,
        model_name: str,
        temperature: float = 0.2,
        max_tokens: int = 5000,
        extra_body: dict = {},
    ):
        # Get usage every time
        extra_body["usage"] = {"include": True}

        # Model settings
        self.model_settings = OpenAIChatModelSettings(
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )
        self.model = OpenAIChatModel(
            model_name=model_name,
            settings=self.model_settings,
            provider=OpenRouterProvider(api_key=openrouter_api_key),
        )
        assert gitlab_client is not None or db_session is not None, (
            "GitlabClient and DB session are required."
        )

        self.gitlab_client = gitlab_client
        self.db_session = db_session

    def gather_context(self, mr: "gitlab.v4.objects.ProjectMergeRequest") -> str:
        """Gather context for the merge request including diffs, title, and description."""
        # Fetch MR details from GitLab
        mr_diffs = mr.diffs.get(mr.diffs.list(page=1, per_page=1)[0].id).diffs

        # Build context string
        context_lines: list[str] = []
        context_lines.append(f"Merge Request Title: {mr.title}")
        context_lines.append(f"Merge Request Description: {mr.description}")
        context_lines.append("")

        ignored_files = []
        for diff in mr_diffs:
            # Skip diffs that are too large (token-based)
            if token_counter(diff.get("diff", "")) > settings.max_tokens_per_diff:
                ignored_files.append(
                    diff.get("new_path", "") or diff.get("old_path", "unknown")
                )
                continue

            # Determine status
            if diff.get("new_file"):
                status = "added"
            elif diff.get("deleted_file"):
                status = "deleted"
            elif diff.get("renamed_file"):
                status = "renamed"
            elif diff.get("generated_file"):
                status = "generated"
            else:
                status = "modified"

            # Determine diff availability
            can_review = (
                not getattr(diff, "too_large", False)
                and not getattr(diff, "collapsed", False)
                and bool(diff.get("diff", "").strip())
            )
            diff_text = diff.get("diff", "").strip() if can_review else None

            # Append file block
            context_lines.append("### File")
            context_lines.append(f"old_path: {diff.get('old_path')}")
            context_lines.append(f"new_path: {diff.get('new_path')}")
            context_lines.append(f"status: {status}")
            context_lines.append(f"can_review_diff: {str(can_review).lower()}")
            context_lines.append("")

            if can_review:
                context_lines.append("Diff:")
                context_lines.append(diff_text)
            else:
                context_lines.append("Diff unavailable")

            context_lines.append("")

        # Summary of skipped files
        if ignored_files:
            context_lines.append(
                f"Note: The following files were skipped due to size constraints: {', '.join(ignored_files)}"
            )

        return "\n".join(context_lines)

    async def run(
        self,
        mr_iid: int,
        project_id: int,
        system_prompt: str = SMART_AGENT_SYSTEM_PROMPT,
        user_prompt: str | None = None,
        message_history: list[ModelMessage] | None = None,
    ) -> None:
        """Run the agent with a user prompt and optional message history. Posts the response as a comment on the MR.

        Args:
            user_prompt: The user's prompt/question
            message_history: Optional list of previous messages for context
        """
        if not user_prompt:
            user_prompt = SMART_AGENT_USER_PROMPT

        # Fetch MR details
        project = self.gitlab_client.projects.get(project_id, lazy=True)
        mr = project.mergerequests.get(mr_iid)

        # Gather context
        context = self.gather_context(mr=mr)

        # Append context to user prompt
        user_prompt = f"{context}\n\n{user_prompt}"

        # Initialize the agent
        self.agent = Agent(
            model=self.model,
            tools=tools_wrapper(
                gitlab_client=self.gitlab_client,
                mr_iid=mr_iid,
                project_id=project_id,
                source_branch=mr.source_branch,
            ),
            system_prompt=system_prompt,
        )

        # Run the agent
        response = await self.agent.run(
            user_prompt=user_prompt,
            message_history=message_history or [],
            usage_limits=UsageLimits(tool_calls_limit=3),
        )

        logger.info(f"SmartAgent response: {response.output}")
        logger.info(f"SmartAgent id: {response.provider_response_id}")
        self._get_openrouter_cost(response.provider_response_id)
        logger.info(f"SmartAgent usage: {response.usage()}")

        # Post the response as a comment on the MR
        mr.notes.create({"body": response.output})

    def _get_openrouter_cost(self, provider_response_id: str):
        url = "https://openrouter.ai/api/v1/generation"

        querystring = {"id": provider_response_id}
        headers = {"Authorization": f"Bearer {self.openrouter_api_key}"}
        response = requests.get(url, headers=headers, params=querystring)
        print(response.json())
