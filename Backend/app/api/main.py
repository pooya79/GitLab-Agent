from fastapi import APIRouter

from app.api.routes import webhooks, user, avatar, llm
from app.core.config import settings

api_router = APIRouter(prefix=f"/api/v{settings.api_version}")
api_router.include_router(user.router)
# api_router.include_router(bot.router)
api_router.include_router(avatar.router)
api_router.include_router(llm.router)
api_router.include_router(webhooks.router)
