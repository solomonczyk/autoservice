import logging
from app.bot.loader import bot

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def notify_client_status_change(chat_id: int, service_name: str, new_status: str):
        """
        Sends a notification to the client about their appointment status change.
        """
        if not chat_id:
            return

        status_messages = {
            "confirmed": f"✅ Ваша запись на услугу «{service_name}» подтверждена!",
            "in_progress": f"🔧 Мастер приступил к работе над вашим автомобилем («{service_name}»).",
            "done": f"🎉 Ваш автомобиль готов! Услуга «{service_name}» выполнена. Ждем вас!",
            "cancelled": f"🚫 К сожалению, ваша запись на «{service_name}» была отменена. Пожалуйста, свяжитесь с нами для уточнения."
        }

        message = status_messages.get(new_status)
        if not message:
            return

        try:
            await bot.send_message(chat_id, message)
            logger.info(f"Notification sent to {chat_id} for status {new_status}")
        except Exception as e:
            logger.error(f"Failed to send notification to {chat_id}: {e}")
