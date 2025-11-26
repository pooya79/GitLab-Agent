from typing import List, Optional, Union

from pydantic import BaseModel, Field

from .command_interface import CommandInterface
from app.prompts.review import system_template, user_template


class RelatedIssue(BaseModel):
    id: str
    title: str
    labels: Optional[List[str]] = None
    description: Optional[str] = None


class ReviewInput(BaseModel):
    title: str
    branch: str
    diff: str
    description: Optional[str] = None
    date: Optional[str] = None
    extra_instructions: Optional[str] = None
    related_issues: Optional[List[RelatedIssue]] = None
    require_estimate_effort_to_review: bool = False
    require_score: bool = False
    require_tests: bool = False
    require_security_review: bool = False
    require_todo_scan: bool = False
    num_max_findings: int = 5
    is_ai_metadata: bool = False
    duplicate_prompt_examples: bool = False


class KeyIssuesComponentLink(BaseModel):
    relevant_file: str
    issue_header: str
    issue_content: str
    start_line: int
    end_line: int


class TodoSection(BaseModel):
    relevant_file: str
    line_number: int
    content: str


class IssueCompliance(BaseModel):
    issue_id: str
    issue_title: str
    issue_description: str
    fully_compliant_points: str
    not_compliant_points: str
    requires_further_human_verification: str


class ReviewBody(BaseModel):
    issue_compliance_check: Optional[List[IssueCompliance]] = None
    estimated_effort_to_review: Optional[int] = Field(
        default=None,
        description="Scale of 1-5 representing the effort to review the MR",
    )
    score: Optional[str] = None
    relevant_tests: Optional[str] = None
    key_issues_to_review: List[KeyIssuesComponentLink] = Field(default_factory=list)
    security_concerns: Optional[str] = None
    todo_sections: Optional[Union[List[TodoSection], str]] = None


class MRReviewOutput(BaseModel):
    review: ReviewBody


class ReviewCommand(CommandInterface):
    async def run(self, flags: dict[str, str | bool], args: list[str]) -> str:
        pass

    def _render_input(self, input_data: ReviewInput) -> str:
        return user_template.render(**input_data.model_dump())

    def _render_system_prompt(self, input_data: ReviewInput) -> str:
        return system_template.render(**input_data.model_dump())
