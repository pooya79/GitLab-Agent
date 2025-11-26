"""Default LLM model configurations available at start."""

from app.db.models import LLMModelInfo

llm_model_infos: list[LLMModelInfo] = [
    LLMModelInfo(
        model_name="openai/gpt-5",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={"reasoning": {"effort": "medium", "exclude": True}},
    ),
    LLMModelInfo(
        model_name="openai/gpt-5-mini",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={"reasoning": {"effort": "medium", "exclude": True}},
    ),
    LLMModelInfo(
        model_name="openai/gpt-4o",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={},
    ),
    LLMModelInfo(
        model_name="openai/gpt-4o-mini",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={},
    ),
    LLMModelInfo(
        model_name="openai/gpt-4.1",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={},
    ),
    LLMModelInfo(
        model_name="openai/gpt-4.1-mini",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={},
    ),
    LLMModelInfo(
        model_name="google/gemini-2.5-pro",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={"thinkingConfig": {"thinkingBudget": 4096}},
    ),
    LLMModelInfo(
        model_name="google/gemini-2.5-flash",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={"thinkingConfig": {"thinkingBudget": 4096}},
    ),
    LLMModelInfo(
        model_name="anthropic/claude-sonnet-4.5",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={"reasoning": {"max_tokens": 4096}},
    ),
    LLMModelInfo(
        model_name="anthropic/claude-haiku-4.5",
        context_window=16384,
        max_output_tokens=16384,
        temperature=0.2,
        additional_kwargs_schema={"reasoning": {"max_tokens": 4096}},
    ),
]
