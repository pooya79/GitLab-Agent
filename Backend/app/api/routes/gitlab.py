from typing import List
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.deps import get_gitlab_accout_token, SessionDep
from app.services.gitlab_service import GitlabService
from app.db.models import Bot
from app.schemas.gitlab import UserInfo, GitlabProject, GitlabProjectsList
from app.core.log import logger


router = APIRouter(prefix="/gitlab", tags=["gitlab"])


@router.get("/userinfo", response_model=UserInfo)
async def get_gitlab_userinfo(
    request: Request, gitlab_oauth_token: str = Depends(get_gitlab_accout_token)
):
    """
    Get GitLab user information for the authenticated user.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    user_info = gitlab_service.get_user_info()
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid GitLab OAuth token")

    user_info = UserInfo(**user_info)

    return user_info


@router.get("/projects", response_model=GitlabProjectsList)
async def list_gitlab_projects(
    session: SessionDep,
    page: int = 1,
    per_page: int = 20,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    list GitLab projects for the authenticated user.
    """
    # Fetch projects from GitLab
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    projects, total = gitlab_service.list_user_projects(page=page, per_page=per_page)
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

    return GitlabProjectsList(
        projects=project_details,
        total=total,
        page=page,
        per_page=per_page,
    )


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
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    List access tokens for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    tokens = gitlab_service.list_project_tokens(project_id)
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
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Get a specific access token for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    token = gitlab_service.get_project_token(project_id, access_token_id)
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
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Create a new access token for a GitLab project.
    """
    body = await request.json()
    access_token_id = body.get("access_token_id")
    scopes = body.get("scopes", [])
    expires_at = body.get("expires_at")

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    token = gitlab_service.create_project_token(
        project_id, access_token_id, scopes, expires_at
    )

    return JSONResponse(content=token)


@router.get("/projects/{project_id}/webhooks")
async def list_gitlab_project_webhooks(
    project_id: str | int,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    List webhooks for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    hooks = gitlab_service.list_webhooks(project_id)
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
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Get a specific webhook for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    hook = gitlab_service.get_webhook(project_id, hook_id)
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
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Create a new webhook for a GitLab project.
    """
    body = await request.json()
    url = body.get("url")
    events = body.get("events", {})

    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    hook = gitlab_service.create_webhook(
        project_id,
        url,
        events,
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
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Delete a webhook for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    gitlab_service.delete_webhook(project_id, hook_id)

    return JSONResponse(content={"detail": "Webhook deleted successfully"})
