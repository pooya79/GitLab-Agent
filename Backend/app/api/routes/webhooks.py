import logging

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import Response

from app.api.deps import SessionDep
from app.db.models import Bot
from app.services.event_handlers import (
    handle_merge_request_event,
    handle_note_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

# map GitLab event names to your handler coroutines
EVENT_HANDLERS = {
    "Merge Request Hook": handle_merge_request_event,
    "Note Hook": handle_note_event,
}


@router.post("/webhooks/{bot_id}")
async def webhook(bot_id: int, request: Request, session: SessionDep) -> Response:
    # load bot
    bot = await session.get(Bot, bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with ID {bot_id} not found.",
        )

    # verify secret token
    gitlab_token = request.headers.get("X-Gitlab-Token")
    if not gitlab_token or gitlab_token != bot.gitlab_webhook_secret:
        logger.warning(f"Invalid webhook token for bot {bot_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token.",
        )

    # dispatch based on event type
    event_type = request.headers.get("X-Gitlab-Event", "")
    payload = await request.json()
    logger.info(f"Webhook event {event_type} for bot: #{bot_id}")

    handler = EVENT_HANDLERS.get(event_type)
    if handler:
        try:
            await handler(bot, payload)
        except HTTPException:
            # let handler-raised HTTPExceptions propagate
            raise
        except Exception:
            logger.exception(f"Error handling {event_type} for bot {bot_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing webhook payload.",
            )
        return Response(status_code=status.HTTP_200_OK)

    # unknown/unhandled event → noop
    logger.info(f"Received unhandled event '{event_type}' for bot {bot_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
