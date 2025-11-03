from pydantic_ai import Agent, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_core import to_jsonable_python
from sqlalchemy import select
import json

from app.services.gitlab_service import GitlabService
from app.db.database import AsyncSession
from app.db.models import ChatHistory
from app.prompts.smart_agent import SMART_AGENT_SYSTEM_PROMPT, SMART_AGENT_USER_PROMPT
from app.services.cache_service import NOW


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
        extra_body: dict = {},
    ):
        # get usage every time
        extra_body["usage"] = {"include": True}

        model_settings = OpenAIChatModelSettings(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=OpenRouterProvider(api_key=api_key),
            extra_body=extra_body,
        )

        assert gitlab_service is not None or db_session is not None, (
            "GitlabService and DB session are required."
        )

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

    async def fetch_history(
        self, mr_id: int, botname: str, username: str, limit: int = 10
    ) -> list[ModelMessage]:
        """Fetch message history from the database and convert to ModelMessage format.

        Args:
            mr_id: The Merge Request ID
            botname: The name of the bot
            username: The username of the person interacting with the bot
            limit: Maximum number of messages to fetch

        Returns:
            List of ModelMessage objects in chronological order (oldest first)
        """
        async with self.db_session() as session:
            history = await session.execute(
                select(ChatHistory)
                .filter(
                    ChatHistory.mr_id == mr_id,
                    ChatHistory.botname == botname,
                    ChatHistory.username == username,
                )
                .order_by(
                    ChatHistory.timestamp.asc()
                )  # oldest first for proper context
                .limit(limit)
            )

            messages = []
            for record in history.scalars().all():
                # Deserialize the stored JSON message back to ModelMessage
                message_data = json.loads(record.message)
                validated_message = ModelMessagesTypeAdapter.validate_python(
                    [message_data]
                )[0]
                messages.append(validated_message)

            return messages

    async def save_message_history(
        self,
        mr_id: int,
        gitlab_project_path: str,
        botname: str,
        username: str,
        messages: list[ModelMessage],
    ):
        """Save a list of ModelMessage objects to the database.

        This should be called after an agent run to persist the conversation history.

        Args:
            gitlab_project_path: The GitLab project path
            botname: The name of the bot
            username: The username of the person interacting with the bot
            messages: List of ModelMessage objects to save
        """
        async with self.db_session() as session:
            for message in messages:
                # Serialize the ModelMessage to JSON
                message_json = json.dumps(to_jsonable_python(message))

                # Determine the role based on the message type
                role = message.kind  # 'request' or 'response'

                chat_message = ChatHistory(
                    mr_id=mr_id,
                    gitlab_project_path=gitlab_project_path,
                    botname=botname,
                    username=username,
                    message=message_json,
                    role=role,
                    timestamp=NOW(),
                )
                session.add(chat_message)

            await session.commit()

    async def run_with_history(
        self,
        user_prompt: str,
        gitlab_project_path: str,
        botname: str,
        username: str,
        limit: int = 10,
    ) -> tuple[str, list[ModelMessage]]:
        """Run the agent with automatic message history management.

        This is a convenience method that:
        1. Fetches the message history from the database
        2. Runs the agent with the user prompt and history
        3. Returns both the output and new messages (which can be saved later)

        Args:
            user_prompt: The user's prompt/question
            gitlab_project_path: The GitLab project path
            botname: The name of the bot
            username: The username of the person interacting
            limit: Maximum number of historical messages to load

        Returns:
            A tuple of (agent_output, new_messages)
            - agent_output: The text response from the agent
            - new_messages: The new messages from this run (to be saved)
        """
        # Fetch existing message history
        message_history = await self.fetch_history(
            gitlab_project_path=gitlab_project_path, botname=botname, limit=limit
        )

        # Run the agent
        result = await self.agent.run(
            user_prompt=user_prompt, message_history=message_history
        )

        # Return both the output and the new messages from this run
        return result.output, result.new_messages()
