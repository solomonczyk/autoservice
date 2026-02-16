from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from app.core.config import settings

def get_main_keyboard() -> ReplyKeyboardMarkup:
    is_https = settings.WEBAPP_URL.startswith("https://")
    
    buttons = []
    if is_https:
        buttons.append([KeyboardButton(text="📅 Записаться", web_app=WebAppInfo(url=settings.WEBAPP_URL))])
    else:
        buttons.append([KeyboardButton(text="📅 Записаться (Нужен HTTPS)")])
    
    buttons.append([KeyboardButton(text="📋 Мои записи")])
    buttons.append([KeyboardButton(text="📱 Поделиться номером", request_contact=True)])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard
