from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from .command_interface import CommandInterface
from app.prompts.describe import system_template, user_template


class MRType(str, Enum):
    bug_fix = "Bug fix"
    tests = "Tests"
    enhancement = "Enhancement"
    documentation = "Documentation"
    other = "Other"


class RelatedIssue(BaseModel):
    id: str
    title: str
    labels: Optional[List[str]] = None
    description: Optional[str] = None


class DescribeInput(BaseModel):
    title: str
    branch: str
    diff: str
    description: Optional[str] = None
    commit_messages_str: Optional[str] = None
    related_issues: Optional[List[RelatedIssue]] = None
    extra_instructions: Optional[str] = None
    enable_diagram: bool = False
    enable_files: bool = False
    enable_file_summary: bool = False
    duplicate_prompt_examples: bool = False


class FileDescription(BaseModel):
    filename: str
    changes_summary: Optional[str] = None
    changes_title: str
    label: str


class MRDescriptionOutput(BaseModel):
    type: List[MRType]
    description: str
    title: str
    changes_diagram: Optional[str] = None
    mr_files: Optional[List[FileDescription]] = None


class DescribeCommand(CommandInterface):
    async def run(
        self,
        project_id: int,
        mr_iid: int,
        flags: dict[str, str | bool],
        args: list[str],
    ) -> str:
        pass

    def _render_input(self, input_data: DescribeInput) -> str:
        return user_template.render(**input_data.model_dump())

    def _render_system_prompt(self, input_data: DescribeInput) -> str:
        return system_template.render(**input_data.model_dump())
