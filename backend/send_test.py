import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot

async def main():
    token = "REDACTED_BOT_TOKEN"
    bot = Bot(token=token)
    user_id = 628292857
    print(f"Sending test message to {user_id}...")
    try:
        await bot.send_message(user_id, "Бот проснулся! Проверка связи.")
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
