from fastapi import APIRouter

from api.routes import bot, webhooks, user, avatar, llm, lara_expert
from core.config import settings

api_router = APIRouter(prefix=f"/api/v{settings.api_version}")
api_router.include_router(user.router)
api_router.include_router(bot.router)
api_router.include_router(avatar.router)
api_router.include_router(llm.router)
api_router.include_router(webhooks.router)


api_router.include_router(lara_expert.router)
