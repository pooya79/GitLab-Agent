from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_gitlab_accout_token, SessionDep
from app.services.gitlab_service import GitlabService


router = APIRouter(prefix="/gitlab", tags=["gitlab"])


@router.get("/userinfo")
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

    return JSONResponse(content=user_info)


@router.get("/projects")
async def get_gitlab_projects(
    page: int = 1,
    per_page: int = 20,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Get GitLab projects for the authenticated user.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    projects = gitlab_service.get_user_projects(page=page, per_page=per_page)
    if not projects:
        raise HTTPException(status_code=401, detail="Invalid GitLab OAuth token")

    # Get Useful details
    project_details = [
        {
            "id": project.id,
            "name_with_namespace": project.name_with_namespace,
            "path_with_namespace": project.path_with_namespace,
            "web_url": project.web_url,
        }
        for project in projects
    ]

    return project_details


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


@router.post("/projects/{project_id}/access-tokens/{access_token_id}/rotate")
async def rotate_gitlab_project_access_token(
    project_id: str | int,
    access_token_id: str | int,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Rotate an existing access token for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    new_token = gitlab_service.rotate_project_token(project_id, access_token_id)

    return JSONResponse(content=new_token)


@router.delete("/projects/{project_id}/access-tokens/{access_token_id}/revoke")
async def revoke_gitlab_project_access_token(
    project_id: str | int,
    access_token_id: str | int,
    gitlab_oauth_token: str = Depends(get_gitlab_accout_token),
):
    """
    Revoke an existing access token for a GitLab project.
    """
    gitlab_service = GitlabService(oauth_token=gitlab_oauth_token)
    gitlab_service.revoke_project_token(project_id, access_token_id)

    return JSONResponse(content={"detail": "Access token revoked successfully"})


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
