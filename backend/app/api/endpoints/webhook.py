from fastapi import APIRouter, Request
from aiogram.types import Update
from app.services.redis_service import RedisService

from app.bot.loader import bot, dp
from app.core.config import settings

router = APIRouter()

@router.post(f"/webhook/{settings.TELEGRAM_BOT_TOKEN}")
async def bot_webhook(update: dict):
    telegram_update = Update(**update)
    
    # Idempotency Check
    redis = RedisService.get_redis()
    update_id = telegram_update.update_id
    key = f"telegram_update:{update_id}"
    
    if await redis.exists(key):
        return {"status": "ok", "msg": "already_processed"}
    
    await redis.set(key, "1", ex=86400) # Expire in 24 hours
    
    await dp.feed_update(bot, telegram_update)
    return {"status": "ok"}
