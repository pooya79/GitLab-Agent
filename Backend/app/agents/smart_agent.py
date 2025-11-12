import gitlab
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_core import to_jsonable_python
from sqlalchemy import select
import json

from app.db.database import AsyncSession
from app.db.models import History
from app.prompts.smart_agent import SMART_AGENT_SYSTEM_PROMPT, SMART_AGENT_USER_PROMPT
from app.agents.utils import token_counter
from app.services.cache_service import NOW
from app.core.config import settings


# Tools
def approve_mr():
    """Tool to approve a GitLab Merge Request."""
    pass


def get_file(file_path: str) -> str:
    """Tool to get the content of a file in the GitLab repository. given its path.
    you can use this tool only 2 times per conversation."""
    pass


class SmartAgent:
    def __init__(
        self,
        openrouter_api_key: str,
        gitlab_client: gitlab.Gitlab,
        db_session: AsyncSession,
        model_name: str,
        system_prompt: str = SMART_AGENT_SYSTEM_PROMPT,
        temperature: float = 0.2,
        max_tokens: int = 5000,
        extra_body: dict = {},
    ):
        # get usage every time
        extra_body["usage"] = {"include": True}

        model_settings = OpenAIChatModelSettings(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=OpenRouterProvider(api_key=openrouter_api_key),
            extra_body=extra_body,
        )

        assert gitlab_client is not None or db_session is not None, (
            "GitlabClient and DB session are required."
        )

        self.gitlab_client = gitlab_client
        self.db_session = db_session

        self.agent = Agent(
            model=OpenAIChatModel(settings=model_settings),
            tools=[approve_mr, get_file],
            usage_limits=UsageLimits(tool_calls_limit=3),
            system_prompt=system_prompt,
        )

    async def gather_context(self, mr_id: int, project_path: str) -> str:
        # Get MR details
        mr_details = self.gitlab_service.get_merge_request(
            project_path=project_path, mr_id=mr_id
        )
        mr_diffs = mr_details.diffs

        # Build context string
        ## See which diffs are small enough
        ignored_diffs = [diff for diff in mr_diffs if token_counter(diff.diff) > settings.max_tokens_per_diff]
        diff_context = ""
        for diff in mr_diffs:
            pass



        context = f"Merge Request Title: {mr_details['title']}\n"
        context += f"Merge Request Description: {mr_details['description']}\n"

    async def run(
        self,
        user_prompt: str = SMART_AGENT_SYSTEM_PROMPT,
        message_history: list[ModelMessage] | None = None,
    ) -> str:
        """Run the agent with a user prompt and optional message history.

        Args:
            user_prompt: The user's prompt/question
            message_history: Optional list of previous messages for context

        Returns:
            The agent's response as a string
        """
        if not user_prompt:
            user_prompt = SMART_AGENT_USER_PROMPT

        response = await self.agent.run(
            user_prompt=user_prompt, message_history=message_history or []
        )
        return response.output
