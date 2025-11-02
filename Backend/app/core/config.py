from pydantic import model_validator, BaseModel
from pydantic_settings import SettingsConfigDict, BaseSettings


class SQLDatabaseSettings(BaseModel):
    url: str


class GitlabSettings(BaseModel):
    base: str
    client_id: str
    client_secret: str
    webhook_ssl_verify: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="_", env_nested_max_split=1)

    # --- grouped sub-settings ---
    sqlite: SQLDatabaseSettings
    gitlab: GitlabSettings

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
    llm_output_tokens: int = 5000
    llm_temperature: float = 0.2
    avatar_default_url: str = "api/static/avatars/default.png"


settings = Settings()
