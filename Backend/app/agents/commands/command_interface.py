from abc import ABC, abstractmethod
import gitlab
from pymongo.database import Database
from pydantic_ai.models import Model


class CommandInterface(ABC):
    def __init__(self, gitlab_client: gitlab.Gitlab, db: Database, llm_model: Model):
        self.gitlab_client = gitlab_client
        self.db = db
        self.llm_model = llm_model

    @abstractmethod
    async def run(self, request_str: str) -> str:
        """
        Execute the command asynchronously.
        Returns a string result.
        """
        pass
