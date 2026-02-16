import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart

async def main():
    token = "REDACTED_BOT_TOKEN"
    bot = Bot(token=token)
    dp = Dispatcher()
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message):
        print(f"Received /start from {message.from_user.id}")
        await message.answer("Test bot is active!")

    dp.include_router(router)
    
    print("Deleting webhook...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Starting bot polling (standalone)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
