from typing import Optional
import gitlab

from app.core.log import logger


def token_counter(text: str) -> int:
    """A simple token counter based on character count."""
    return len(text) // 4  # Approximate 4 characters per token


def emphasize_header(text: str, only_markdown=False, reference_link=None) -> str:
    try:
        # Finding the position of the first occurrence of ": "
        colon_position = text.find(": ")

        # Splitting the string and wrapping the first part in <strong> tags
        if colon_position != -1:
            # Everything before the colon (inclusive) is wrapped in <strong> tags
            if only_markdown:
                if reference_link:
                    transformed_string = (
                        f"[**{text[: colon_position + 1]}**]({reference_link})\n"
                        + text[colon_position + 1 :]
                    )
                else:
                    transformed_string = (
                        f"**{text[: colon_position + 1]}**\n"
                        + text[colon_position + 1 :]
                    )
            else:
                if reference_link:
                    transformed_string = (
                        f"<strong><a href='{reference_link}'>{text[: colon_position + 1]}</a></strong><br>"
                        + text[colon_position + 1 :]
                    )
                else:
                    transformed_string = (
                        "<strong>"
                        + text[: colon_position + 1]
                        + "</strong>"
                        + "<br>"
                        + text[colon_position + 1 :]
                    )
        else:
            # If there's no ": ", return the original string
            transformed_string = text

        return transformed_string
    except Exception as e:
        logger.exception(f"Failed to emphasize header: {e}")
        return text


def fetch_file(
    gitlab_client: gitlab.Gitlab,
    project_id: int,
    file_path: str,
    ref: str,
) -> Optional[str]:
    """
    Fetch the content of a file from a GitLab repository.

    Args:
        gitlab_client: An authenticated GitLab client instance.
        project_id: The ID of the GitLab project.
        file_path: The path to the file in the repository.
        ref: The branch, tag, or commit SHA to fetch the file from.
    Returns:
        The content of the file as a string, or None if not found.
    """
    try:
        project = gitlab_client.projects.get(project_id, lazy=True)
        file = project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode("utf-8")
    except Exception as e:
        logger.error(
            f"Failed to fetch file {file_path} from project {project_id} at ref {ref}: {e}"
        )
        return None


def get_line_link(
    gl_url: str,
    project_path: str,
    source_branch: str,
    relevant_file: str,
    relevant_line_start: int,
    relevant_line_end: Optional[int] = None,
    *,
    github_style_range: bool = False,
) -> str:
    """
    Build a GitLab blob URL for a file in the MR source branch with optional line anchors.

    Args:
        gl_url: Base GitLab URL (e.g., "https://gitlab.example.com").
        project_path: Project path with namespace (e.g., "group/project").
        source_branch: Branch name to link against.
        relevant_file: File path (relative to repo root).
        relevant_line_start: Start line number (-1 for whole-file link).
        relevant_line_end: Optional end line number for a range.
        github_style_range: If True, use "#Lstart-Lend" (GitHub style).
                            If False (default), use GitLab style "#Lstart" and "#Lend".

    Returns:
        A string with the blob URL.
    """
    relevant_file = relevant_file.strip().strip("`").lstrip("/")

    base = (
        f"{gl_url}/{project_path}/-/blob/{source_branch}/{relevant_file}?ref_type=heads"
    )

    if relevant_line_start == -1:
        return base

    if relevant_line_end:
        if github_style_range:
            # GitHub style ranges
            return f"{base}#L{relevant_line_start}-L{relevant_line_end}"
        else:
            # GitLab style anchors (two separate anchors, works in web UI)
            return f"{base}#L{relevant_line_start}-L{relevant_line_end}"
    else:
        return f"{base}#L{relevant_line_start}"
