import asyncio
import sys
import logging

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.bot.loader import bot, dp
from app.bot.handlers import router as bot_router

async def main():
    logger.info("Starting bot standalone...")
    dp.include_router(bot_router)
    
    # Ensure webhook is deleted
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("Bot is polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
