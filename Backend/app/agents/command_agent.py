from typing import Callable
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.services.gitlab_service import GitlabService
from app.db.database import AsyncSession


class CommandAgent:
    commands: dict[str, Callable] = {
        "review": None,
        "describe": None,
        "suggest": None,
        "add_docs": None,
    }

    def __init__(
        self,
        api_key: str,
        gitlab_service: GitlabService,
        db_session: AsyncSession,
        model_name: str,
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

        assert gitlab_service is not None or db_session is not None, (
            "GitlabService and DB session are required."
        )
        self.gitlab_service = gitlab_service
        self.db_session = db_session

        self.model = OpenAIChatModel(settings=model_settings)

    async def run(
        self,
        input_command: str,
    ) -> str:
        pass

    def _init_agent(self, system_prompt: str) -> Agent:
        return Agent(
            model=self.model,
            tools=[],
            system_prompt=system_prompt,
        )
    
    
