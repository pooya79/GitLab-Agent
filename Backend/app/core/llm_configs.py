from typing import Any
from pydantic import BaseModel


class AvailableLlm(BaseModel):
    llm_model: str
    llm_max_output_tokens: int
    llm_temperature: float
    llm_additional_kwargs: dict[str, Any] | None = None


available_llms: dict[str, AvailableLlm] = {
    "openai/gpt-5": AvailableLlm(
        llm_model="openai/gpt-5",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"effort": "medium", "exclude": True}},
    ),
    "openai/gpt-5-mini": AvailableLlm(
        llm_model="openai/gpt-5-mini",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"effort": "medium", "exclude": True}},
    ),
    "openai/gpt-4o": AvailableLlm(
        llm_model="openai/gpt-4o",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    "openai/gpt-4o-mini": AvailableLlm(
        llm_model="openai/gpt-4o-mini",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    "openai/gpt-4.1": AvailableLlm(
        llm_model="openai/gpt-4.1",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    "openai/gpt-4.1-mini": AvailableLlm(
        llm_model="openai/gpt-4.1-mini",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs=None,
    ),
    "google/gemini-2.5-pro": AvailableLlm(
        llm_model="google/gemini-2.5-pro",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"thinkingConfig": {"thinkingBudget": 4096}},
    ),
    "google/gemini-2.5-flash": AvailableLlm(
        llm_model="google/gemini-2.5-flash",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"thinkingConfig": {"thinkingBudget": 4096}},
    ),
    "anthropic/claude-sonnet-4.5": AvailableLlm(
        llm_model="anthropic/claude-sonnet-4.5",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"max_tokens": 4096}},
    ),
    "anthropic/claude-haiku-4.5": AvailableLlm(
        llm_model="anthropic/claude-haiku-4.5",
        llm_max_output_tokens=16384,
        llm_temperature=0.2,
        llm_additional_kwargs={"reasoning": {"max_tokens": 4096}},
    ),
}
