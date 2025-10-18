from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

oauth = OAuth()
oauth.register(
    name="gitlab",
    client_id=settings.gitlab.client_id,
    client_secret=settings.gitlab.client_secret,
    server_metadata_url=f"{settings.gitlab.base}/.well-known/openid-configuration",
    access_token_url=f"{settings.gitlab.base}/oauth/token",
    authorize_url=f"{settings.gitlab.base}/oauth/authorize",
    api_base_url=f"{settings.gitlab.base}/api/v4",
    client_kwargs={
        "scope": "openid profile email read_user",  # add what you need
        "token_endpoint_auth_method": "client_secret_post",  # GitLab accepts body auth
    },
)
