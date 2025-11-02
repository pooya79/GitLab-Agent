from pydantic_ai import Agent, UsageLimits
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.services.gitlab_service import GitlabService
from app.db.database import AsyncSession
from app.prompts.smart_agent import SMART_AGENT_SYSTEM_PROMPT, SMART_AGENT_USER_PROMPT


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
        api_key: str,
        gitlab_service: GitlabService,
        db_session: AsyncSession,
        model_name: str,
        system_prompt: str = SMART_AGENT_SYSTEM_PROMPT,
        temperature: float = 0.2,
        max_tokens: int = 5000,
        extra_body: dict = None,
    ):
        model_settings = OpenAIChatModelSettings(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=OpenRouterProvider(api_key=api_key),
            extra_body=extra_body or {},
        )

        assert gitlab_service is not None or db_session is not None, "GitlabService and DB session are required."

        self.gitlab_service = gitlab_service
        self.db_session = db_session
        
        self.agent = Agent(
            model=OpenAIChatModel(settings=model_settings),
            tools=[approve_mr, get_file],
            usage_limits=UsageLimits(tool_calls_limit=3),
            system_prompt=system_prompt,
        )

    async def run(
        self,
        user_prompt: str = SMART_AGENT_SYSTEM_PROMPT,
        message_history: list[ModelMessage] | None = None,
    ) -> str:
        if not user_prompt:
            user_prompt = SMART_AGENT_USER_PROMPT

        if message_history is None:
            message_history = await self.fetch_history(limit=4)

        response = self.agent.run(
            user_prompt=user_prompt, message_history=message_history
        )
        return response

    async def fetch_history(self, limit: int = 10) -> list[ModelMessage]:
        pass
