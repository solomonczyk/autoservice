import json
import logging
from datetime import datetime, timedelta
from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.bot.keyboards import get_main_keyboard
from app.db.session import async_session_local
from app.models.models import Client, Appointment, Service, AppointmentStatus
from app.core.slots import get_available_slots
from app.services.redis_service import RedisService
from app.core.config import settings

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
        result = await db.execute(
            select(Client)
            .where(Client.telegram_id == message.from_user.id)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            await message.answer("У вас пока нет записей. Пожалуйста, поделитесь номером для регистрации.")
            return

        stmt = select(Appointment).options(joinedload(Appointment.service)).where(
            and_(
                Appointment.client_id == client.id,
                Appointment.status != AppointmentStatus.CANCELLED
            )
        ).order_by(Appointment.start_time.desc())
        
        result = await db.execute(stmt)
        appointments = result.scalars().all()
        
        if not appointments:
            await message.answer("У вас пока нет активных записей.")
            return
            
        for appt in appointments:
            text = (
                f"Запись #{appt.id}\n"
                f"🛠 Услуга: {appt.service.name}\n"
                f"📅 Время: {appt.start_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 Статус: {appt.status.value}"
            )
            
            # Create inline keyboard for each appointment
            webapp_url = f"{settings.WEBAPP_URL}?appointment_id={appt.id}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Изменить время", web_app=WebAppInfo(url=webapp_url)),
                    InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_appt:{appt.id}")
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("cancel_appt:"))
async def cancel_appointment_handler(callback_query: Message):
    appt_id = int(callback_query.data.split(":")[1])
    async with async_session_local() as db:
        appt = await db.get(Appointment, appt_id)
        if appt:
            appt.status = AppointmentStatus.CANCELLED
            await db.commit()
            await callback_query.message.edit_text(
                f"Запись #{appt_id} успешно отменена. ❌"
            )
            
            # Broadcast update to dashboard
            redis = RedisService.get_redis()
            message = {
                "type": "STATUS_UPDATE",
                "data": {
                    "id": appt.id,
                    "shop_id": appt.shop_id,
                    "status": "cancelled"
                }
            }
            await redis.publish("appointments_updates", json.dumps(message))
        else:
            await callback_query.answer("Запись не найдена.")

@router.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        service_id = data.get("service_id")
        date_str = data.get("date")
        appointment_id = data.get("appointment_id")
        is_waitlist = data.get("is_waitlist", False)
        
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

            # Check for existing appointment if rescheduling
            existing_appt = None
            if appointment_id:
                existing_appt = await db.get(Appointment, int(appointment_id))
                if not existing_appt:
                    await message.answer("Ошибка: Исходная запись не найдена.")
                    return

            if not is_waitlist:
                available_slots = await get_available_slots(
                    shop_id=1,
                    service_duration_minutes=service.duration_minutes,
                    date=start_time_naive.date(),
                    db=db,
                    exclude_appointment_id=int(appointment_id) if appointment_id else None
                )
                
                if not any(slot == start_time_naive for slot in available_slots):
                    await message.answer("Извините, это время уже занято. Пожалуйста, выберите другое.")
                    return

            if not appointment_id:
                # Create new client or find existing
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
            else:
                client = await db.get(Client, existing_appt.client_id)

            end_time = start_time_naive + timedelta(minutes=service.duration_minutes)

            status = AppointmentStatus.WAITLIST if is_waitlist else (AppointmentStatus.CONFIRMED if appointment_id else AppointmentStatus.NEW)

            if appointment_id:
                existing_appt.service_id = service_id
                existing_appt.start_time = start_time_naive
                existing_appt.end_time = end_time
                existing_appt.status = status
                appt = existing_appt
            else:
                new_appt = Appointment(
                    shop_id=1,
                    client_id=client.id,
                    service_id=service_id,
                    start_time=start_time_naive,
                    end_time=end_time,
                    status=status
                )
                db.add(new_appt)
                appt = new_appt
            
            await db.commit()
            await db.refresh(appt)
            
            if is_waitlist:
                msg = (
                    f"📝 Ваша заявка добавлена в лист ожидания!\n\n"
                    f"Услуга: {service.name}\n"
                    f"Желаемая дата: {start_time_naive.strftime('%d.%m.%Y')}\n\n"
                    f"Если освободится место, мастер свяжется с вами для уточнения деталей."
                )
            else:
                action_text = "изменена" if appointment_id else "подтверждена"
                msg = (
                    f"✅ Запись {action_text}!\n\n"
                    f"Услуга: {service.name}\n"
                    f"Время: {start_time_naive.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Мы ждем вас!"
                )
            
            await message.answer(msg)

            try:
                redis = RedisService.get_redis()
                event_type = "WAITLIST_ADD" if is_waitlist else ("APPOINTMENT_UPDATED" if appointment_id else "NEW_APPOINTMENT")
                broadcast_message = {
                    "type": event_type,
                    "data": {
                        "id": appt.id,
                        "shop_id": appt.shop_id,
                        "start_time": appt.start_time.isoformat(),
                        "status": appt.status.value
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
    if not message.text:
        return

    # Treat any unhandled text as a request for consultation
    from app.services.ai_service import ai_service
    from aiogram.utils.chat_action import ChatActionSender

    async with async_session_local() as db:
        # 1. Fetch all services for AI context
        result = await db.execute(select(Service))
        services = result.scalars().all()

        # 2. Show "typing" indicator
        async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
            # 3. Get AI response
            response = await ai_service.get_consultation(
                user_message=message.text,
                services=services
            )
            
            # 4. Reply to user
            await message.answer(response)
