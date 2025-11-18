import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pymongo.database import Database

from app.api.deps import get_mongo_database
from app.db.models import Bot
from app.services.event_handlers import handle_merge_request_event, handle_note_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

# map GitLab event names to your handler coroutines
EVENT_HANDLERS = {
    "Merge Request Hook": handle_merge_request_event,
    "Note Hook": handle_note_event,
}


@router.post("/webhooks/{bot_user_id}")
async def webhook(
    bot_user_id: int, request: Request, mongo_db: Database = Depends(get_mongo_database)
) -> Response:
    # load bot (based on the user_id attribute)
    bot = Bot.from_document(mongo_db["bots"].find_one({"gitlab_user_id": bot_user_id}))
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with user id {bot_user_id} not found.",
        )

    # verify secret token
    gitlab_token = request.headers.get("X-Gitlab-Token")
    if not gitlab_token or gitlab_token != bot.gitlab_webhook_secret:
        logger.warning(f"Invalid webhook token for bot {bot.id}: {bot.name}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token.",
        )

    # dispatch based on event type
    event_type = request.headers.get("X-Gitlab-Event", "")
    payload = await request.json()
    logger.info(f"Webhook event {event_type} for bot: #{bot.id}")

    handler = EVENT_HANDLERS.get(event_type)
    if handler:
        try:
            await handler(bot, payload)
        except HTTPException:
            # let handler-raised HTTPExceptions propagate
            raise
        except Exception:
            logger.exception(f"Error handling {event_type} for bot {bot.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing webhook payload.",
            )
        return Response(status_code=status.HTTP_200_OK)

    # unknown/unhandled event → noop
    logger.info(f"Received unhandled event '{event_type}' for bot {bot.id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
