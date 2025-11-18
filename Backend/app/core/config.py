from typing import Any

from pydantic import model_validator, BaseModel
from pydantic_settings import SettingsConfigDict, BaseSettings


class SQLDatabaseSettings(BaseModel):
    url: str


class GitlabSettings(BaseModel):
    base: str
    client_id: str
    client_secret: str
    webhook_ssl_verify: bool = True


class AvailableLlm(BaseModel):
    llm_model: str
    llm_max_output_tokens: int
    llm_temperature: float
    llm_additional_kwargs: dict[str, Any] | None = None


available_llms = [
    AvailableLlm(
        llm_model="openai/gpt-5",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"effort": "medium", "exclude": True}},
    ),
    AvailableLlm(
        llm_model="openai/gpt-5-mini",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"effort": "medium", "exclude": True}},
    ),
    AvailableLlm(
        llm_model="openai/gpt-4o",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    AvailableLlm(
        llm_model="openai/gpt-4o-mini",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    AvailableLlm(
        llm_model="openai/gpt-4.1",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    AvailableLlm(
        llm_model="openai/gpt-4.1-mini",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    AvailableLlm(
        llm_model="google/gemini-2.5-pro",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"thinkingConfig": {"thinkingBudget": 4096}},
    ),
    AvailableLlm(
        llm_model="google/gemini-2.5-flash",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"thinkingConfig": {"thinkingBudget": 4096}},
    ),
    AvailableLlm(
        llm_model="anthropic/claude-sonnet-4.5",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"max_tokens": 4096}},
    ),
    AvailableLlm(
        llm_model="anthropic/claude-haiku-4.5",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"max_tokens": 4096}},
    ),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1)

    # --- grouped sub-settings ---
    sqlite: SQLDatabaseSettings
    gitlab: GitlabSettings
    llms: list[AvailableLlm] = available_llms

    # --- individual settings ---
    project_name: str = "Gitlab Agent"
    api_version: int = 1

    host: str = "http://"
    port: int = 8000
    host_url: str

    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    log_dir: str = "logs"
    data_dir: str = "/data"  # don't change it

    @model_validator(mode="after")
    def _fill_host_url(self):
        if not self.host_url:
            object.__setattr__(self, "host_url", f"{self.host}:{self.port}")
        return self

    ## Security settings
    secret_key: str = "test"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    ## Admin User
    admin_username: str
    admin_email: str
    admin_password: str

    ## External services
    openrouter_api_base: str = "https://openrouter.ai"
    openrouter_api_key: str | None = None
    logfire_token: str | None = None

    ## Default Agents Configs
    max_chat_history: int = 10
    llm_model: str = "openai/gpt-4o-mini"
    llm_context_window: int = 40000
    llm_max_output_tokens: int = 5000
    llm_temperature: float = 0.2
    avatar_default_url: str = "api/static/avatars/default.png"
    max_tokens_per_diff: int = 4000
    max_tokens_per_context: int = 20000


settings = Settings()
