from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from app.core.config import settings


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main reply keyboard with branded buttons."""
    is_https = settings.WEBAPP_URL.startswith("https://")

    buttons = []
    if is_https:
        buttons.append([
            KeyboardButton(
                text="🔧 Записаться на сервис",
                web_app=WebAppInfo(url=settings.WEBAPP_URL)
            )
        ])
    else:
        buttons.append([KeyboardButton(text="🔧 Записаться (⚠️ нужен HTTPS)")])

    buttons.append([
        KeyboardButton(text="📋 Мои записи"),
        KeyboardButton(text="💬 Консультация"),
    ])
    buttons.append([
        KeyboardButton(text="📱 Отправить номер", request_contact=True)
    ])
    buttons.append([
        KeyboardButton(text="📄 Правовая информация")
    ])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="✍️ Напишите вопрос или выберите действие..."
    )


def get_appointment_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for a single appointment card."""
    webapp_url = f"{settings.WEBAPP_URL}?appointment_id={appointment_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Перенести",
                web_app=WebAppInfo(url=webapp_url)
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"cancel_appt:{appointment_id}"
            ),
        ]
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Simple 'back to menu' inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")]
    ])
