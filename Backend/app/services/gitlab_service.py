import gitlab
from gitlab.v4.objects import Project, ProjectAccessToken, ProjectHook

from app.core.config import settings

GitLabAccessLevel = gitlab.const.AccessLevel


class GitlabService:
    def __init__(self, oauth_token: str):
        self.base_url = settings.gitlab.base
        self.oauth_token = oauth_token
        self.gl = gitlab.Gitlab(self.base_url, oauth_token=oauth_token)

    def get_user_info(self):
        try:
            self.gl.auth()
            user = self.gl.user
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "web_url": user.web_url,
            }
        except gitlab.GitlabAuthenticationError:
            return None

    def list_user_projects(
        self, page: int = 1, per_page: int = 20
    ) -> tuple[list[Project], int]:
        # Fetch projects with at least Maintainer access
        # Fetch a lot so that we can count number of projects easily
        projects = self.gl.projects.list(
            get_all=True,
            min_access_level=GitLabAccessLevel.MAINTAINER,
        )

        total = len(projects)

        projects = projects[page - 1 : page - 1 + per_page]

        return projects, total

    def get_user_project(self, project_id: str | int) -> Project:
        project = self.gl.projects.get(project_id)
        return project

    def list_project_tokens(self, project_id: str | int) -> list[ProjectAccessToken]:
        tokens = self.gl.projects.get(project_id, lazy=True).access_tokens.list()
        return tokens

    def get_project_token(
        self, project_id: str | int, access_token_id: str | int
    ) -> ProjectAccessToken:
        token = self.gl.projects.get(project_id, lazy=True).access_tokens.get(
            access_token_id
        )
        return token

    def create_project_token(
        self,
        project_id: str | int,
        access_token_name: str,
        scopes: list[str],
        expires_at: str | None = None,
    ) -> ProjectAccessToken:
        token = self.gl.projects.get(project_id, lazy=True).access_tokens.create(
            {"name": access_token_name, "scopes": scopes, "expires_at": expires_at}
        )
        return token

    def rotate_project_token(
        self, project_id: str | int, access_token_id: str | int
    ) -> ProjectAccessToken:
        new_token = self.gl.projects.get(project_id, lazy=True).access_tokens.rotate(
            access_token_id
        )
        return new_token

    def revoke_project_token(
        self, project_id: str | int, access_token_id: str | int
    ) -> None:
        self.gl.projects.get(project_id, lazy=True).access_tokens.delete(
            access_token_id
        )

    def list_webhooks(
        self, project_id: str | int
    ) -> list[gitlab.v4.objects.ProjectHook]:
        hooks = self.gl.projects.get(project_id, lazy=True).hooks.list()
        return hooks

    def get_webhook(self, project_id: str | int, hook_id: str | int) -> ProjectHook:
        hook = self.gl.projects.get(project_id, lazy=True).hooks.get(hook_id)
        return hook

    def create_webhook(
        self,
        project_id: str | int,
        url: str,
        events: dict,
        enable_ssl_verification: bool = True,
        token: str | None = None,
    ) -> ProjectHook:
        hook_data = {
            "url": url,
            "enable_ssl_verification": enable_ssl_verification,
            "token": token,
        }
        hook_data.update(events)
        hook = self.gl.projects.get(project_id, lazy=True).hooks.create(hook_data)
        return hook

    def delete_webhook(self, project_id: str | int, hook_id: str | int) -> None:
        self.gl.projects.get(project_id, lazy=True).hooks.delete(hook_id)
