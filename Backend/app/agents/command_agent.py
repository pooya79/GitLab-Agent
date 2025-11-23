from typing import Callable
import gitlab
from pymongo.database import Database

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider


class CommandAgent:
    commands: dict[str, Callable] = {
        "review": None,
        "describe": None,
        "suggest": None,
        "add_docs": None,
    }

    def __init__(
        self,
        openrouter_api_key: str,
        gitlab_client: gitlab.Gitlab,
        mongo_db: Database,
        model_name: str,
        temperature: float = 0.2,
        max_tokens: int = 5000,
        extra_body: dict = None,
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
        self.gitlab_client = gitlab_client
        self.mongo_db = mongo_db

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
