from typing import List, Optional

from pydantic import BaseModel

from .command_interface import CommandInterface
from app.prompts.suggest import (
    reflect_system_template,
    reflect_user_template,
    system_template,
    user_template,
)


class CodeSuggestion(BaseModel):
    relevant_file: str
    language: str
    existing_code: str
    suggestion_content: str
    improved_code: str
    one_sentence_summary: str
    label: str


class MRCodeSuggestionsOutput(BaseModel):
    code_suggestions: List[CodeSuggestion]


class SuggestInput(BaseModel):
    title: str
    diff: str
    num_code_suggestions: int
    date: Optional[str] = None
    extra_instructions: Optional[str] = None
    focus_only_on_problems: bool = False
    is_ai_metadata: bool = False
    duplicate_prompt_examples: bool = False


class SuggestCommand:
    def __init__(self) -> None:
        pass

    async def run(
        self,
        project_id: int,
        mr_iid: int,
        flags: dict[str, str | bool],
        args: list[str],
    ) -> str:
        pass

    def _render_input(self, input_data: SuggestInput) -> str:
        return user_template.render(**input_data.model_dump())

    def _render_system_prompt(self, input_data: SuggestInput) -> str:
        return system_template.render(**input_data.model_dump())


class CodeSuggestionFeedback(BaseModel):
    suggestion_summary: str
    relevant_file: str
    relevant_lines_start: int
    relevant_lines_end: int
    suggestion_score: int
    why: str


class MRCodeSuggestionsFeedbackOutput(BaseModel):
    code_suggestions: List[CodeSuggestionFeedback]


class SuggestFeedbackInput(BaseModel):
    diff: str
    suggestion_str: str
    num_code_suggestions: int
    duplicate_prompt_examples: bool = False


class SuggestFeedbackCommand(CommandInterface):
    async def run(self, flags: dict[str, str | bool], args: list[str]) -> str:
        pass

    def _render_input(self, input_data: SuggestFeedbackInput) -> str:
        return reflect_user_template.render(**input_data.model_dump())

    def _render_system_prompt(self, input_data: SuggestFeedbackInput) -> str:
        return reflect_system_template.render(**input_data.model_dump())
