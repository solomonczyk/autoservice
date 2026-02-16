import json
import logging
from datetime import datetime, timedelta
from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from app.bot.keyboards import get_main_keyboard
from app.db.session import async_session_local
from app.models.models import Client, Appointment, Service, AppointmentStatus
from app.core.slots import get_available_slots
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    async with async_session_local() as db:
        stmt = select(Client).where(Client.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if client:
            await message.answer(
                f"Рады видеть вас снова, {client.full_name}! 👋\nЧем могу помочь сегодня?",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"Привет, {html.bold(message.from_user.full_name)}! 👋\nЯ помогу вам записаться в наш автосервис.\n\n"
                "Для более точной записи, пожалуйста, нажмите кнопку «📱 Поделиться номером» ниже.",
                reply_markup=get_main_keyboard()
            )

@router.message(F.contact)
async def contact_handler(message: Message):
    contact = message.contact
    phone = contact.phone_number.replace("+", "")
    
    async with async_session_local() as db:
        stmt = select(Client).where(Client.phone == phone)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if client:
            client.telegram_id = message.from_user.id
            await db.commit()
            await message.answer(
                f"Спасибо, {client.full_name}! Ваш номер {phone} привязан к вашей учетной записи. ✅",
                reply_markup=get_main_keyboard()
            )
        else:
            new_client = Client(
                full_name=message.from_user.full_name,
                phone=phone,
                telegram_id=message.from_user.id
            )
            db.add(new_client)
            await db.commit()
            await message.answer(
                "Приятно познакомиться! Ваш номер успешно зарегистрирован. Теперь вы можете записываться на услуги. 🚗💨",
                reply_markup=get_main_keyboard()
            )

@router.message(F.text == "📅 Записаться (Нужен HTTPS)")
async def need_https_handler(message: Message):
    await message.answer(
        "⚠️ **Telegram требует HTTPS** для работы Mini Apps.\n\n"
        "Для работы кнопки записи локально вам нужно:\n"
        "1. Использовать туннель (например, **ngrok**).\n"
        "2. Указать полученный `https://...` адрес в `.env` (переменная `WEBAPP_URL`).\n\n"
        "Пока что вы можете протестировать интерфейс просто в браузере: http://localhost:5173/webapp"
    )

@router.message(F.text == "📋 Мои записи")
async def my_appointments(message: Message):
    async with async_session_local() as db:
        result = await db.execute(select(Client).where(Client.telegram_id == message.from_user.id))
        client = result.scalar_one_or_none()
        
        if not client:
            await message.answer("У вас пока нет записей. Пожалуйста, поделитесь номером для регистрации.")
            return

        stmt = select(Appointment).where(Appointment.client_id == client.id).order_by(Appointment.start_time.desc())
        result = await db.execute(stmt)
        appointments = result.scalars().all()
        
        if not appointments:
            await message.answer("У вас пока нет записей.")
            return
            
        text = "Ваши записи:\n\n"
        for appt in appointments:
            # Fetch service name if needed, but for MVP let's keep it simple
            text += f"📅 {appt.start_time.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"Статус: {appt.status.value}\n\n"
            
        await message.answer(text)

@router.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        service_id = data.get("service_id")
        date_str = data.get("date")
        
        if not service_id or not date_str:
            await message.answer("Ошибка: Некорректные данные от приложения.")
            return

        start_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        start_time_naive = start_time.replace(tzinfo=None)
        
        async with async_session_local() as db:
            service = await db.get(Service, service_id)
            if not service:
                 await message.answer("Ошибка: Услуга не найдена.")
                 return

            available_slots = await get_available_slots(
                shop_id=1,
                service_duration_minutes=service.duration_minutes,
                date=start_time_naive.date(),
                db=db
            )
            
            if not any(slot == start_time_naive for slot in available_slots):
                await message.answer("Извините, это время уже занято. Пожалуйста, выберите другое.")
                return

            stmt = select(Client).where(Client.telegram_id == message.from_user.id)
            result = await db.execute(stmt)
            client = result.scalar_one_or_none()
            
            if not client:
                client = Client(
                    telegram_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    phone="unknown"
                )
                db.add(client)
                await db.flush()
                
            end_time = start_time_naive + timedelta(minutes=service.duration_minutes)

            new_appt = Appointment(
                shop_id=1,
                client_id=client.id,
                service_id=service_id,
                start_time=start_time_naive,
                end_time=end_time,
                status=AppointmentStatus.NEW
            )
            
            db.add(new_appt)
            await db.commit()
            await db.refresh(new_appt)
            
            await message.answer(
                f"✅ Запись подтверждена!\n\n"
                f"Услуга: {service.name}\n"
                f"Время: {start_time_naive.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Мы ждем вас! Если что-то изменится, пожалуйста, сообщите нам."
            )

            try:
                redis = RedisService.get_redis()
                broadcast_message = {
                    "type": "NEW_APPOINTMENT",
                    "data": {
                        "id": new_appt.id,
                        "shop_id": new_appt.shop_id,
                        "start_time": new_appt.start_time.isoformat()
                    }
                }
                await redis.publish("appointments_updates", json.dumps(broadcast_message))
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

    except Exception as e:
        logger.error(f"Exception in web_app_data_handler: {e}")
        await message.answer("Произошла ошибка при обработке вашей заявки. Пожалуйста, попробуйте еще раз.")

@router.message()
async def any_message(message: Message):
    logger.debug(f"Received message from {message.from_user.id}: {message.text or message.content_type}")
