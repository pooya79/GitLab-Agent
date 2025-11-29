from abc import ABC, abstractmethod
from typing import Optional, List
import re
import gitlab
from pymongo.database import Database

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from app.db.models import Bot
from app.core.config import settings
from app.core.log import logger
from app.agents.utils import token_counter


class RelatedIssue(BaseModel):
    id: str
    title: str
    labels: Optional[List[str]] = None
    description: Optional[str] = None


class CommandInterface(ABC):
    def __init__(
        self,
        gitlab_client: gitlab.Gitlab,
        mongo_db: Database,
        bot: Bot,
        model: OpenAIChatModel,
    ):
        self.gitlab_client = gitlab_client
        self.mongo_db = mongo_db
        self.bot = bot
        self.model = model

    @abstractmethod
    async def run(
        self,
        project_id: int,
        mr_iid: int,
        flags: dict[str, str | bool],
        args: list[str],
    ) -> str:
        """
        Execute the command asynchronously.
        Returns a string result.
        """
        pass

    def build_agent(
        self,
        system_prompt: str,
        output_type: BaseModel,
    ) -> None:
        self.agent = Agent(
            model=self.model,
            system_prompt=system_prompt,
            output_type=output_type,
        )

    async def gether_gitlab_data(
        self, project_id: int, mr_iid: int
    ) -> dict[str, object]:
        """Fetch MR metadata, diff, and related issues from GitLab."""
        data: dict[str, object] = {
            "title": "",
            "branch": "",
            "diff": "",
            "description": None,
            "related_issues": [],
        }

        try:
            project = self.gitlab_client.projects.get(project_id, lazy=True)
            mr = project.mergerequests.get(mr_iid)
        except gitlab.GitlabError as exc:
            logger.error(
                "Failed to fetch MR %s in project %s: %s", mr_iid, project_id, str(exc)
            )
            return data

        data["title"] = mr.title
        data["branch"] = mr.source_branch
        data["description"] = mr.description

        try:
            data["diff"] = self._gether_gitlab_diff(mr)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "Failed to build diff for MR %s in project %s: %s",
                mr_iid,
                project_id,
                str(exc),
            )

        issue_ids = self._extract_issue_iids(mr.title, mr.description)
        related_issues: list[RelatedIssue] = []

        for issue_iid in issue_ids:
            try:
                issue = project.issues.get(issue_iid)
                related_issues.append(
                    RelatedIssue(
                        id=f"#{issue_iid}",
                        title=issue.title or "",
                        labels=issue.labels or [],
                        description=issue.description or "",
                    )
                )
            except gitlab.GitlabError as exc:
                logger.error(
                    "Failed to fetch issue #%s in project %s: %s",
                    issue_iid,
                    project_id,
                    str(exc),
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Unexpected error fetching issue #%s in project %s: %s",
                    issue_iid,
                    project_id,
                    str(exc),
                )

        data["related_issues"] = related_issues

        return data

    def _gether_gitlab_diff(self, mr: "gitlab.v4.objects.ProjectMergeRequest") -> str:
        """Gather context for the merge request including diffs, title, and description."""
        try:
            diff_versions = mr.diffs.list(page=1, per_page=1)
            latest_version = diff_versions[0] if diff_versions else None
            if latest_version is None:
                logger.warning("No diff versions found for MR %s", mr.iid)
                return ""
            mr_diffs = mr.diffs.get(latest_version.id).diffs
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "Failed to fetch diff for MR %s: %s",
                getattr(mr, "iid", "unknown"),
                str(exc),
            )
            return ""

        context_lines: list[str] = [
            f"Merge Request Title: {mr.title}",
            f"Merge Request Description: {mr.description}",
            "",
        ]

        ignored_files: list[str] = []
        for diff in mr_diffs:
            diff_text = diff.get("diff", "") or ""
            # Skip diffs that are too large (token-based)
            if token_counter(diff_text) > settings.max_tokens_per_diff:
                ignored_files.append(
                    diff.get("new_path", "") or diff.get("old_path", "unknown")
                )
                continue

            if diff.get("new_file"):
                status = "added"
            elif diff.get("deleted_file"):
                status = "deleted"
            elif diff.get("renamed_file"):
                status = "renamed"
            elif diff.get("generated_file"):
                status = "generated"
            else:
                status = "modified"

            can_review = (
                not getattr(diff, "too_large", False)
                and not getattr(diff, "collapsed", False)
                and bool(diff_text.strip())
            )

            context_lines.append(
                f"## File: '{diff.get('new_path') or diff.get('old_path') or 'unknown'}'"
            )
            context_lines.append(f"old_path: {diff.get('old_path')}")
            context_lines.append(f"new_path: {diff.get('new_path')}")
            context_lines.append(f"status: {status}")
            context_lines.append(f"can_review_diff: {str(can_review).lower()}")
            context_lines.append("")

            if can_review:
                formatted_diff = self._format_diff_with_line_numbers(diff_text)
                context_lines.append("Diff:")
                context_lines.append(formatted_diff)
            else:
                context_lines.append("Diff unavailable")

            context_lines.append("")

        if ignored_files:
            context_lines.append(
                "Note: The following files were skipped due to size constraints: "
                + ", ".join(ignored_files)
            )

        return "\n".join(context_lines)

    @staticmethod
    def _format_diff_with_line_numbers(diff_text: str) -> str:
        """Add line numbers to added/removed lines based on hunk headers."""

        def _format_prefix(line_no: int | None) -> str:
            return f"{line_no}".rjust(6) if line_no is not None else " " * 6

        formatted_lines: list[str] = []
        old_line_no: int | None = None
        new_line_no: int | None = None

        for line in diff_text.splitlines():
            if line.startswith("@@"):
                match = re.search(r"@@\s+-([0-9]+)(?:,[0-9]+)?\s+\+([0-9]+)", line)
                if match:
                    old_line_no = int(match.group(1))
                    new_line_no = int(match.group(2))
                formatted_lines.append(line)
                continue

            if line.startswith("+") and not line.startswith("+++"):
                formatted_lines.append(f"{_format_prefix(new_line_no)} {line}")
                if new_line_no is not None:
                    new_line_no += 1
                continue

            if line.startswith("-") and not line.startswith("---"):
                formatted_lines.append(f"{_format_prefix(old_line_no)} {line}")
                if old_line_no is not None:
                    old_line_no += 1
                continue

            if line.startswith(" ") or line.startswith("\t"):
                if old_line_no is not None:
                    old_line_no += 1
                if new_line_no is not None:
                    new_line_no += 1
                formatted_lines.append(line)
                continue

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    @staticmethod
    def _extract_issue_iids(title: str | None, description: str | None) -> list[int]:
        """Return unique issue IIDs mentioned as #<number> in the title or description."""
        combined_text = f"{title or ''}\n{description or ''}"
        issue_ids: list[int] = []
        seen: set[int] = set()

        for match in re.findall(r"(?<!\w)#(\d+)", combined_text):
            issue_iid = int(match)
            if issue_iid not in seen:
                seen.add(issue_iid)
                issue_ids.append(issue_iid)

        return issue_ids
