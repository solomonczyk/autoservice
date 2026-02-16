import logging
from typing import List, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.models import Service

logger = logging.getLogger(__name__)

class AIService:
    _instance: Optional['AIService'] = None
    _client: Optional[AsyncOpenAI] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            if settings.OPENAI_API_KEY:
                cls._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                logger.warning("OPENAI_API_KEY not set. AI consultations will be disabled.")
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
4. Если клиент хочет записаться, вежливо попросите его нажать кнопку "📅 Записаться" внизу или использовать Mini App. 
5. Отвечайте на русском языке. Кратко и по делу.
"""

        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return "Произошла ошибка при обращении к ИИ. Пожалуйста, попробуйте позже или используйте меню."

# Singleton instance
ai_service = AIService()
