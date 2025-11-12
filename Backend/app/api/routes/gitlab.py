from typing import List
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
import gitlab

from app.api.deps import get_gitlab_client, SessionDep
from app.db.models import Bot
from app.schemas.gitlab import UserInfo, GitlabProject, GitlabProject
from app.core.log import logger


router = APIRouter(prefix="/gitlab", tags=["gitlab"])


@router.get("/userinfo", response_model=UserInfo)
async def get_gitlab_userinfo(
    request: Request, gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client)
):
    """
    Get GitLab user information for the authenticated user.
    """
    gitlab_client.auth()
    user_info = gitlab_client.user
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid GitLab OAuth token")

    user_info = UserInfo(
        username=user_info.username,
        email=user_info.email,
        name=user_info.name,
        avatar_url=user_info.avatar_url,
        web_url=user_info.web_url,
    )

    return user_info


@router.get("/projects", response_model=List[GitlabProject])
async def list_gitlab_projects(
    session: SessionDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    list GitLab projects for the authenticated user.
    """
    # Fetch projects from GitLab
    projects = gitlab_client.projects.list(page=page, per_page=per_page, search=search)
    if not projects:
        raise HTTPException(status_code=401, detail="Invalid GitLab OAuth token")

    # Get their bots
    result = await session.execute(
        select(Bot).where(
            Bot.gitlab_project_path.in_(
                [project.path_with_namespace for project in projects]
            )
        )
    )
    bots = result.scalars().all()
    project_bots = {bot.gitlab_project_path: bot for bot in bots}

    # Get Useful details
    project_details = [
        GitlabProject(
            id=project.id,
            name_with_namespace=project.name_with_namespace,
            path_with_namespace=project.path_with_namespace,
            web_url=project.web_url,
            access_level=_extract_access_level(project.permissions),
            bot_id=project_bots.get(project.path_with_namespace).id
            if project.path_with_namespace in project_bots
            else None,
            bot_name=project_bots.get(project.path_with_namespace).name
            if project.path_with_namespace in project_bots
            else None,
            avatar_url=project_bots.get(project.path_with_namespace).avatar_url
            if project.path_with_namespace in project_bots
            else None,
        )
        for project in projects
    ]

    return project_details


def _extract_access_level(permissions: dict[str, dict]):
    access_level = 0
    if permissions["project_access"]:
        access_level = permissions["project_access"]["access_level"]
    if permissions["group_access"]:
        access_level = max(access_level, permissions["group_access"]["access_level"])
    return access_level


@router.get("/projects/{project_id}/access-tokens")
async def list_gitlab_project_access_tokens(
    project_id: str | int,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    List access tokens for a GitLab project.
    """
    tokens = gitlab_client.projects.get(project_id, lazy=True).access_tokens.list()
    if not tokens:
        raise HTTPException(status_code=404, detail="No access tokens found")

    token_list = []
    for token in tokens:
        token_dict = {
            "id": token.id,
            "name": token.name,
            "scopes": token.scopes,
            "expires_at": token.expires_at,
        }
        token_list.append(token_dict)

    return token_list


@router.get("/projects/{project_id}/access-tokens/{access_token_id}")
async def get_gitlab_project_access_token(
    project_id: str | int,
    access_token_id: str | int,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    Get a specific access token for a GitLab project.
    """
    token = gitlab_client.projects.get(project_id, lazy=True).access_tokens.get(
        access_token_id
    )
    if not token:
        raise HTTPException(status_code=404, detail="Access token not found")

    if token is None:
        raise HTTPException(status_code=404, detail="Access token not found")

    token_dict = {
        "id": token.id,
        "name": token.name,
        "scopes": token.scopes,
        "expires_at": token.expires_at,
    }

    return token_dict


@router.post("/projects/{project_id}/access-tokens")
async def create_gitlab_project_access_token(
    project_id: str | int,
    request: Request,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    Create a new access token for a GitLab project.
    """
    body = await request.json()
    access_token_id = body.get("access_token_id")
    scopes = body.get("scopes", [])
    expires_at = body.get("expires_at")

    token = gitlab_client.projects.get(project_id, lazy=True).access_tokens.create(
        {
            "name": access_token_id,
            "scopes": scopes,
            "expires_at": expires_at,
        }
    )

    return JSONResponse(content=token)


@router.get("/projects/{project_id}/webhooks")
async def list_gitlab_project_webhooks(
    project_id: str | int,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    List webhooks for a GitLab project.
    """
    hooks = gitlab_client.projects.get(project_id, lazy=True).hooks.list()
    if not hooks:
        raise HTTPException(status_code=404, detail="No webhooks found")

    hook_list = []
    for hook in hooks:
        hook_dict = {
            "id": hook.id,
            "url": hook.url,
            "merge_requests_events": hook.merge_requests_events,
            "note_events": hook.note_events,
            "created_at": hook.created_at,
        }
        hook_list.append(hook_dict)

    return hook_list


@router.get("/projects/{project_id}/webhooks/{hook_id}")
async def get_gitlab_project_webhook(
    project_id: str | int,
    hook_id: str | int,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    Get a specific webhook for a GitLab project.
    """
    hook = gitlab_client.projects.get(project_id, lazy=True).hooks.get(hook_id)
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    hook_dict = {
        "id": hook.id,
        "url": hook.url,
        "merge_requests_events": hook.merge_requests_events,
        "note_events": hook.note_events,
        "created_at": hook.created_at,
    }

    return hook_dict


@router.post("/projects/{project_id}/webhooks")
async def create_gitlab_project_webhook(
    project_id: str | int,
    request: Request,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    Create a new webhook for a GitLab project.
    """
    body = await request.json()
    url = body.get("url")
    events = body.get("events", {})

    hook = gitlab_client.projects.get(project_id, lazy=True).hooks.create(
        {
            "url": url,
            **events,
        }
    )

    hook_dict = {
        "id": hook.id,
        "url": hook.url,
        "merge_requests_events": hook.merge_requests_events,
        "note_events": hook.note_events,
        "created_at": hook.created_at,
    }

    return hook_dict


@router.delete("/projects/{project_id}/webhooks/{hook_id}")
async def delete_gitlab_project_webhook(
    project_id: str | int,
    hook_id: str | int,
    gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client),
):
    """
    Delete a webhook for a GitLab project.
    """
    gitlab_client.projects.get(project_id, lazy=True).hooks.delete(hook_id)

    return JSONResponse(content={"detail": "Webhook deleted successfully"})
