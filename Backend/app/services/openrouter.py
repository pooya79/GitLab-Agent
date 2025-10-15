import os
from urllib.parse import quote
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, ValidationError

from app.core.log import logger
from app.core.config import settings


class OpenRouterBaseClient:
    API_BASE: str = settings.openrouter_api_base or "https://openrouter.ai"

    def __init__(self, token: Optional[str] = None, **client_opts: Any):
        """
        Initialize the async client with an token.
        Any extra httpx.AsyncClient kwargs (timeout, limits, etc.) go in client_opts.
        """
        token = token or settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if token:
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
        self._client = httpx.AsyncClient(
            base_url=self.API_BASE, headers=headers, **client_opts
        )

    def _url_encode(self, text: str) -> str:
        return quote(text, safe="")

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        resp = await self._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()

    async def _delete(self, path: str) -> None:
        resp = await self._client.delete(path)
        resp.raise_for_status()

    async def close(self) -> None:
        """Cleanly close the underlying HTTP session."""
        await self._client.aclose()


# --------------------
# Pydantic schemas for Models API
# --------------------


class Architecture(BaseModel):
    input_modalities: List[str]
    output_modalities: List[str]
    tokenizer: str
    instruct_type: Optional[str] = None


class TopProvider(BaseModel):
    is_moderated: bool
    context_length: Optional[float] = None
    max_completion_tokens: Optional[float] = None


class Pricing(BaseModel):
    prompt: str
    completion: str
    image: str
    request: str
    web_search: str
    internal_reasoning: Optional[str] = None
    input_cache_read: Optional[str] = None
    input_cache_write: Optional[str] = None


class Model(BaseModel):
    id: str
    name: str
    created: float
    description: str
    architecture: Architecture
    top_provider: TopProvider
    pricing: Pricing
    canonical_slug: Optional[str] = None
    context_length: Optional[float] = None
    hugging_face_id: Optional[str] = None
    per_request_limits: Optional[Dict[str, Any]] = None
    supported_parameters: Optional[List[str]] = None


class ModelsResponse(BaseModel):
    data: List[Model]


class OpenRouterClient(OpenRouterBaseClient):
    def __init__(self, token: Optional[str] = None, **client_opts: Any):
        super().__init__(token, **client_opts)

    async def get_models(self) -> List[Model]:
        """
        Fetch all available models from OpenRouter and return as Pydantic Model instances.
        """
        response_json = await self._get("/api/v1/models")
        data = response_json.get("data", [])
        models: List[Any] = []
        for item in data:
            try:
                model = Model(**item)
                models.append(model)
            except ValidationError as e:
                logger.error(
                    "Model validation failed for id=%s, name:%s: %s",
                    item.get("id"),
                    item.get("name"),
                    e,
                )
        return models

    async def __aenter__(self) -> "OpenRouterClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
