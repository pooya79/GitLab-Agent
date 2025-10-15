import logging
import asyncio
import re
import httpx
from typing import List, Optional, Set, Dict, Any
from pydantic import HttpUrl

from agents.command_agent.agent import CommandAgent, CommandTypes
from agents.command_agent.schemas import MRDetails, IssueRef, DiffBundle
from agents.llm_factory import LLMFactory
from clients.gitlab import GitlabClient
from models.bot import Bot
from app.core.config import settings

logger = logging.getLogger(__name__)


ISSUE_REF_RE = re.compile(r"(?<!\w)#(\d+)\b")


def _mr_url_from_event(project_web_url: str, iid: int, note_url: str | None) -> str:
    """
    Prefer the note's URL (strip anchor) when available; fallback to canonical MR URL.
    """
    if note_url:
        base = note_url.split("#", 1)[0]
        return base
    return f"{project_web_url}/merge_requests/{iid}"


def _extract_issue_ids(text: Optional[str]) -> List[int]:
    if not text:
        return []
    seen: Set[int] = set()
    for m in ISSUE_REF_RE.finditer(text):
        num = int(m.group(1))
        if num not in seen:
            seen.add(num)
    return list(seen)


async def _fetch_issue_ref(
    aclient: GitlabClient,
    project_id: int | str,
    issue_iid: int,
    project_web_url: str,
) -> IssueRef:
    try:
        issue: Dict[str, Any] = await aclient.issues.get_issue(project_id, issue_iid)
    except Exception as e:
        logger.warning(
            "Failed to fetch issue #%s for project %s: %s", issue_iid, project_id, e
        )
        return None

    # Labels may come as list[str] or list[dict]
    raw_labels = issue.get("labels", [])
    if raw_labels and isinstance(raw_labels[0], dict):
        labels = [
            lbl.get("name")
            for lbl in raw_labels
            if isinstance(lbl, dict) and lbl.get("name")
        ]
    else:
        labels = [str(x) for x in raw_labels]

    return IssueRef(
        id=f"#{issue_iid}",
        title=issue.get("title"),
        description=issue.get("description"),
        labels=labels,
        url=f"{project_web_url}/-/issues/{issue_iid}",
    )


async def _return_empty_list():
    return []


async def _get_languages(
    aclient: GitlabClient,
    project_id: int | str,
):
    try:
        # pass project_id if your client requires it
        return await aclient.projects.get_languages(project_id)
    except Exception as e:
        logger.warning("Failed to fetch project languages for %s: %s", project_id, e)
        return None


def _map_diff_item_to_bundle(item: Dict[str, Any]) -> DiffBundle:
    # GitLab diffs typically include these keys. We normalize and provide safe fallbacks.
    return DiffBundle(
        old_path=item.get("old_path"),
        new_path=item.get("new_path") or item.get("new_path", ""),  # required
        diff=item.get("diff") or item.get("patch") or "",
        new_file=bool(item.get("new_file", False)),
        renamed_file=bool(item.get("renamed_file", False)),
        deleted_file=bool(item.get("deleted_file", False)),
        generated_file=bool(item.get("generated_file", False)),  # GitLab 16.9+
    )


async def _fetch_diffs(
    aclient: GitlabClient,
    project_id: int | str,
    mr_iid: int,
) -> List[DiffBundle]:
    """
    Fetch MR diffs via your aclient.list_changes and map them to DiffBundle.
    Your helper hits: GET /projects/:id/merge_requests/:iid/diffs
    """
    resp: (
        Dict[str, Any] | List[Dict[str, Any]]
    ) = await aclient.merge_requests.list_changes(
        project_id=project_id,
        merge_request_iid=mr_iid,
    )

    # Normalize response shape:
    if isinstance(resp, list):
        diffs_raw = resp
    else:
        # try common containers
        diffs_raw = resp.get("diffs") or resp.get("changes") or []

    return [_map_diff_item_to_bundle(it) for it in diffs_raw]


async def build_mr_details(
    event_payload: Dict,
    aclient: GitlabClient,
    user_description: Optional[str] = None,
):
    mr = event_payload["merge_request"]
    project = event_payload["project"]
    obj = event_payload["object_attributes"]

    project_id = project["id"]
    mr_iid = mr["iid"]
    project_web_url = str(project["web_url"])

    # URL to MR (strip note anchor if present)
    mr_url = _mr_url_from_event(
        project_web_url=project_web_url,
        iid=mr_iid,
        note_url=str(obj["url"]) if obj and obj["url"] else None,
    )

    # Labels -> titles list
    label_titles = [lbl["title"] for lbl in (mr["labels"] or [])]

    # Last commit (that's all the webhook gives)
    commit_messages = (
        [mr["last_commit"]["message"]]
        if mr["last_commit"] and mr["last_commit"]["message"]
        else []
    )
    latest_commit_sha = mr["last_commit"]["id"] if mr["last_commit"] else None
    latest_commit_url = (
        str(mr["last_commit"]["url"])
        if (mr["last_commit"] and mr["last_commit"]["url"])
        else None
    )

    # IDs from MR description (add obj.note if you want refs from the comment too)
    issue_ids = _extract_issue_ids(mr["description"])

    # Fetch diffs + issues + project languages concurrently
    diffs_coro = _fetch_diffs(aclient, project_id, mr_iid)
    issue_coros = [
        _fetch_issue_ref(aclient, project_id, iid, project_web_url) for iid in issue_ids
    ]
    issues_coro = asyncio.gather(*issue_coros) if issue_coros else _return_empty_list()
    langs_coro = _get_languages(aclient, project_id)

    diffs, fetched_issues, project_languages = await asyncio.gather(
        diffs_coro,
        issues_coro,
        langs_coro,
    )

    # Filter out failed issue fetches (None)
    issues = [iss for iss in fetched_issues if iss is not None]

    # Build MRDetails
    details = MRDetails(
        gl_url=settings.gitlab_base,
        project_token=aclient.token,
        # Identity / routing
        mr_id=str(mr_iid),
        mr_url=mr_url,  # HttpUrl will validate
        # Core metadata
        title=mr["title"],
        source_branch=mr["source_branch"],
        target_branch=mr["target_branch"],
        description=mr["description"],
        labels=label_titles,
        user_description=user_description,
        project_languages=project_languages,
        # Project
        project_id=project_id,
        project_name=project["path_with_namespace"],
        # Commits
        commit_messages=commit_messages,  # <- full history
        latest_commit_sha=latest_commit_sha,
        latest_commit_url=latest_commit_url,
        # Diffs
        diffs=diffs,
        # Issues (parsed from description; titles/labels/descriptions)
        issues=issues,
    )

    return details


async def command_handler(full_command: str, bot: Bot, event_payload: Dict):
    # Clean the command string
    cmd = full_command.strip()

    # Create the LLM
    llm = LLMFactory.get_llm(
        model="openai/gpt-5-mini-2025-08-07",
        # model="openai/gpt-5",
        max_tokens=10000,
        context_window=128000,
        temperature=0.2,
        is_function_calling_model=True,
    )

    # Create MR details required by agent
    async with GitlabClient(bot.gitlab_access_token) as gitlab_client:
        logging.info("Building MR details for command agent.")
        mr_details = await build_mr_details(event_payload, gitlab_client)

        cmd_input = CommandTypes(command=cmd, mr=mr_details)

        # Create agent and run
        agent = CommandAgent(llm)
        agent_response = await agent.run(cmd_input)

        if not agent_response:
            logger.error(
                "Agent failed to create a valid response (response is either empty or None)"
            )

        try:
            mr_iid = event_payload["merge_request"]["iid"]
            project_id = event_payload["project_id"]
            post_resp = await gitlab_client.merge_requests.create_note(
                project_id=project_id,
                merge_request_iid=mr_iid,
                body=agent_response,
            )
            logger.info(
                f"Posted reply note {post_resp.get('id')} to MR !{mr_iid} in project {bot.gitlab_project_path}"
            )
        except httpx.HTTPStatusError as e:
            # non-2xx response
            status = e.response.status_code
            text = e.response.text
            logger.error(
                f"Failed to post reply to MR !{mr_iid}: HTTP {status} – {text}"
            )
        except httpx.RequestError as e:
            # network/transport error
            logger.error(f"Network error posting MR reply: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error posting MR reply: {e}")
