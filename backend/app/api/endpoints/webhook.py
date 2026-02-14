from fastapi import APIRouter, Request
from aiogram.types import Update

from app.bot.loader import bot, dp
from app.core.config import settings

router = APIRouter()

@router.post(f"/webhook/{settings.TELEGRAM_BOT_TOKEN}")
async def bot_webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"status": "ok"}
