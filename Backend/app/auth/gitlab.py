import httpx
from typing import Optional
import base64
import os
import hashlib

from app.core.config import settings


class GitlabAuthService:
    def __init__(self):
        self.base_url = settings.gitlab.base

    # --- PKCE + state helpers ---
    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @classmethod
    def new_pkce(cls) -> tuple[str, str]:
        code_verifier = cls._b64url(os.urandom(64))
        code_challenge = cls._b64url(hashlib.sha256(code_verifier.encode()).digest())
        return code_verifier, code_challenge

    @classmethod
    def new_state(cls) -> str:
        return cls._b64url(os.urandom(32))

    # --- OAuth2 flow methods ---
    def build_authorize_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        scope: Optional[str] = None,
    ) -> str:
        params = {
            "client_id": settings.gitlab.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if scope:
            params["scope"] = scope

        url = f"{self.base_url}/oauth/authorize?" + str(httpx.QueryParams(params))
        return str(url)

    async def exchange_code_for_token(
        self,
        client: httpx.AsyncClient,
        redirect_uri: str,
        code: str,
        code_verifier: str,
    ) -> dict:
        data = {
            "client_id": settings.gitlab.client_id,
            "client_secret": settings.gitlab.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        response = await client.post(f"{self.base_url}/oauth/token", data=data)
        response.raise_for_status()
        return response.json()

    async def refresh_token(
        self, client: httpx.AsyncClient, refresh_token: str
    ) -> dict:
        data = {
            "client_id": settings.gitlab.client_id,
            "client_secret": settings.gitlab.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        response = await client.post(f"{self.base_url}/oauth/token", data=data)
        response.raise_for_status()
        return response.json()

    async def revoke_token(
        self, client: httpx.AsyncClient, token: str, hint: str = "refresh_token"
    ) -> None:
        data = {
            "client_id": settings.gitlab.client_id,
            "client_secret": settings.gitlab.client_secret,
            "token": token,
            "token_type_hint": hint,
        }
        response = await client.post(f"{self.base_url}/oauth/revoke", data=data)
        response.raise_for_status()

    async def get_userinfo(self, client: httpx.AsyncClient, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{self.base_url}/api/v4/user", headers=headers)
        response.raise_for_status()
        return response.json()
