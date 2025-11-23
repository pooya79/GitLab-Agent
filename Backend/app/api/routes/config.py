from fastapi import APIRouter

from app.core.llm_configs import AvailableLlm, available_llms

router = APIRouter(
    prefix="/config",
    tags=["config"],
)

AVAILABLE_BOT_AVATARS = [
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


@router.get("/available-avatars", response_model=list[str])
async def get_available_avatars():
    """
    Get a list of available bot avatars.
    """
    return AVAILABLE_BOT_AVATARS


@router.get("/available-llms", response_model=dict[str, AvailableLlm])
async def get_available_llms():
    """
    Get a list of available LLM models.
    """
    return available_llms
