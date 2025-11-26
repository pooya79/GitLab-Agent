from .command_interface import CommandInterface

from app.core.config import settings


class HelpCommand(CommandInterface):
    async def run(self, flags: dict[str, str | bool], args: list[str]) -> str:
        return f"""## Smart Agent — Help

Invoke the Smart Agent by typing `@<bot_name>` or `@<bot_username>` anywhere in your message.  
Example: `@bot how can I improve this code?`

• You may edit the Smart Agent’s system prompt from the GitLab Agent Dashboard.  
• The Smart Agent has access to previous comments in the same thread, allowing continuous conversation.  
• You may also assign the Smart Agent as a reviewer on a merge request.

## Command Agent — Help

Invoke the Command Agent by typing `@<bot_name>/<command>` or `@<bot_username>/<command>` at the **start** of your message.  
Example: `@project_90_bot_b4a2e933c93d73e105430f3224e52815/help`

Available commands:
- `/help` — Show this help message.
- `/review` — Review the merge request for code quality and compliance. **(Not implemented)**
- `/describe` — Describe the merge request and its changes. **(Not implemented)**
- `/suggest` — Suggest code improvements. **(Not implemented)**
- `/add_docs` — Add or update documentation related to the merge request. **(Not implemented)**

GitLab Agent Dashboard: {settings.frontend_url}"""
