from typing import List, Optional, Literal

from pydantic import BaseModel

from .command_interface import CommandInterface
from app.prompts.add_docs import system_template, user_template


class AddDocsInput(BaseModel):
    title: str
    branch: str
    diff: str
    docs_for_language: str
    language: Optional[str] = None
    description: Optional[str] = None
    extra_instructions: Optional[str] = None


class AddDocsDocumentation(BaseModel):
    relevant_file: str
    relevant_line: int
    doc_placement: Literal["before", "after"]
    documentation: str


class AddDocsOutput(BaseModel):
    code_documentation: List[AddDocsDocumentation]


class AddDocsCommand(CommandInterface):
    async def run(
        self,
        project_id: int,
        mr_iid: int,
        flags: dict[str, str | bool],
        args: list[str],
    ) -> str:
        pass

    def _render_input(self, input_data: AddDocsInput) -> str:
        return user_template.render(**input_data.model_dump())

    def _render_system_prompt(self, input_data: AddDocsInput) -> str:
        return system_template.render(**input_data.model_dump())
