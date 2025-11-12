from fastapi import APIRouter

from app.core.config import settings, AvailableLlm

router = APIRouter(
    prefix="/config",
    tags=["config"],
)

AVAILABLE_BOT_AVATARS = {
    avatar_name: f"{settings.backend_url}/api/static/avatars/{avatar_name}"
    for avatar_name in [
        "8-bit_bot",
        "analyst",
        "cyber_samurai",
        "default",
        "galactic_bot",
        "hacker",
        "khosro",
        "librarian",
        "steampunk",
    ]
}



@router.get("/available-avatars", response_model=dict[str, str])
async def get_available_avatars():
    """
    Get a list of available bot avatars.
    """
    return AVAILABLE_BOT_AVATARS

@router.get("/available-llms", response_model=list[AvailableLlm])
async def get_available_llms():
    """
    Get a list of available LLM models.
    """
    return settings.llms