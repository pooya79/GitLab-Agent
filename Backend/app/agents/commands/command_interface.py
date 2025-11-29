from abc import ABC, abstractmethod
import gitlab
from pymongo.database import Database

from pydantic import BaseModel
from pydantic_ai import (
    Agent,
    UsageLimits,
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
    AgentRunResult,
    ModelMessagesTypeAdapter,
)
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

from app.db.models import Bot


class CommandInterface(ABC):
    def __init__(
        self,
        gitlab_client: gitlab.Gitlab,
        mongo_db: Database,
        bot: Bot,
        model: OpenAIChatModel,
    ):
        self.gitlab_client = gitlab_client
        self.mongo_db = mongo_db
        self.bot = bot
        self.model = model

    @abstractmethod
    async def run(
        self,
        project_id: int,
        mr_iid: int,
        flags: dict[str, str | bool],
        args: list[str],
    ) -> str:
        """
        Execute the command asynchronously.
        Returns a string result.
        """
        pass

    def build_agent(
        self,
        system_prompt: str,
        output_type: BaseModel,
    ) -> None:
        self.agent = Agent(
            model=self.model,
            system_prompt=system_prompt,
            output_type=output_type,
        )

        
