import logging
from typing import List, Optional
from gigachat import GigaChat
from app.core.config import settings
from app.models.models import Service

logger = logging.getLogger(__name__)

class AIService:
    _instance: Optional['AIService'] = None
    _client: Optional[GigaChat] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            if settings.GIGACHAT_CLIENT_SECRET:
                try:
                    # GIGACHAT_CLIENT_SECRET is already a base64-encoded authorization key
                    cls._client = GigaChat(
                        credentials=settings.GIGACHAT_CLIENT_SECRET,
                        scope="GIGACHAT_API_PERS",
                        verify_ssl_certs=False
                    )
                    logger.info("GigaChat client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize GigaChat: {e}")
                    cls._client = None
            else:
                logger.warning("GIGACHAT credentials not set. AI consultations will be disabled.")
        return cls._instance

    async def get_consultation(self, user_message: str, services: List[Service]) -> str:
        if not self._client:
            return "Извините, сейчас я могу отвечать только на стандартные команды. (AI не настроен)"

        # 1. Prepare context from services
        services_info = "\n".join([
            f"- {s.name}: {s.base_price} руб. (длительность: {s.duration_minutes} мин.)"
            for s in services
        ])

        system_prompt = f"""
Вы — опытный и дружелюбный мастер-консультант в автосервисе. 
Ваша задача — помогать клиентам, отвечать на их вопросы о ремонте автомобилей и консультировать по услугам нашего сервиса.

Наши услуги и цены:
{services_info}

Правила общения:
1. Будьте вежливы и профессиональны.
2. Если клиент описывает проблему (например, "что-то стучит"), предложите подходящую услугу из списка (например, диагностику подвески).
3. Если клиент спрашивает цену, назовите её из списка выше.
4. Если клиент просит записать его на конкретное время или дату, вежливо объясните: "К сожалению, у меня пока нет доступа к календарю мастеров для прямой записи. Пожалуйста, нажмите кнопку '📅 Записаться' ниже 👇 или используйте наше мини-приложение для выбора удобного времени."
5. Отвечайте на русском языке. Кратко и по делу.
"""

        try:
            # Prepare payload for GigaChat
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = self._client.chat(payload)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GigaChat error: {e}")
            return "Произошла ошибка при обращении к ИИ. Пожалуйста, попробуйте позже или используйте меню."

# Singleton instance
ai_service = AIService()
