from abc import ABC, abstractmethod
import gitlab
from pymongo.database import Database

from app.db.models import Bot


class CommandInterface(ABC):
    def __init__(self, gitlab_client: gitlab.Gitlab, mongo_db: Database, bot: Bot):
        self.gitlab_client = gitlab_client
        self.mongo_db = mongo_db
        self.bot = bot

    @abstractmethod
    async def run(self, flags: dict[str, str | bool], args: list[str]) -> str:
        """
        Execute the command asynchronously.
        Returns a string result.
        """
        pass
