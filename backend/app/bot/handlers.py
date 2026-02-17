import json
import logging
from datetime import datetime, timedelta, timezone as tz
from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.db.session import async_session_local
from app.models.models import Client, Appointment, Service, AppointmentStatus
from app.bot.keyboards import get_main_keyboard, get_appointment_keyboard
from app.core.slots import get_available_slots
from app.services.redis_service import RedisService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = Router()

# ──────────────────────────────────────────────
#  Message Templates
# ──────────────────────────────────────────────

STATUS_EMOJI = {
    "new": "🆕",
    "confirmed": "✅",
    "in_progress": "🔧",
    "completed": "✔️",
    "cancelled": "❌",
    "waitlist": "📝",
}


def _welcome_msg(name: str, returning: bool = False) -> str:
    if returning:
        return (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 <b>С возвращением, {html.quote(name)}!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Рады видеть вас снова в <b>AutoService</b>.\n"
            f"Чем могу помочь сегодня?\n\n"
            f"🔧 — Записаться на сервис\n"
            f"📋 — Просмотреть записи\n"
            f"💬 — Задать вопрос мастеру"
        )
    return (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚗 <b>Добро пожаловать в AutoService!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Привет, <b>{html.quote(name)}</b>!\n"
        f"Я помогу вам записаться в наш автосервис.\n\n"
        f"📱 <b>Первый шаг</b> — отправьте номер телефона\n"
        f"кнопкой ниже для регистрации.\n\n"
        f"<i>После этого вам станут доступны\n"
        f"запись, консультация и история визитов.</i>"
    )


def _contact_linked_msg(name: str, phone: str) -> str:
    return (
        f"✅ <b>Номер привязан!</b>\n\n"
        f"👤 {html.quote(name)}\n"
        f"📞 <code>{phone}</code>\n\n"
        f"Теперь вы можете записываться на услуги.\n"
        f"Нажмите <b>🔧 Записаться на сервис</b> ниже."
    )


def _contact_new_msg() -> str:
    return (
        f"🎉 <b>Регистрация завершена!</b>\n\n"
        f"Ваш номер сохранён.\n"
        f"Теперь вы можете записываться на услуги 🚗💨\n\n"
        f"Нажмите <b>🔧 Записаться на сервис</b> ниже."
    )


def _appointment_card(appt, show_actions: bool = True) -> str:
    status = appt.status.value if hasattr(appt.status, 'value') else str(appt.status)
    emoji = STATUS_EMOJI.get(status, "📌")
    time_str = appt.start_time.strftime('%d.%m.%Y  %H:%M')

    status_labels = {
        "new": "Новая",
        "confirmed": "Подтверждена",
        "in_progress": "В работе",
        "completed": "Завершена",
        "cancelled": "Отменена",
        "waitlist": "Лист ожидания",
    }
    status_label = status_labels.get(status, status)

    return (
        f"┌─────────────────────\n"
        f"│ {emoji} <b>{appt.service.name}</b>\n"
        f"│\n"
        f"│ 📅  {time_str}\n"
        f"│ 📊  {status_label}\n"
        f"│ 🆔  #{appt.id}\n"
        f"└─────────────────────"
    )


def _booking_confirmed_msg(service_name: str, time_str: str, is_edit: bool = False) -> str:
    action = "перенесена" if is_edit else "подтверждена"
    return (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Запись {action}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔧 <b>Услуга:</b> {html.quote(service_name)}\n"
        f"🕐 <b>Время:</b> {time_str}\n\n"
        f"<i>Мы ждём вас! Если планы изменятся,\n"
        f"вы можете перенести или отменить запись\n"
        f"в разделе 📋 Мои записи.</i>"
    )


def _waitlist_msg(service_name: str, date_str: str) -> str:
    return (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Лист ожидания</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔧 <b>Услуга:</b> {html.quote(service_name)}\n"
        f"📅 <b>Дата:</b> {date_str}\n\n"
        f"<i>Если освободится место, мы свяжемся\n"
        f"с вами для уточнения деталей.</i>"
    )


# ──────────────────────────────────────────────
#  Handlers
# ──────────────────────────────────────────────

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    async with async_session_local() as db:
        stmt = select(Client).where(Client.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()

        if client:
            await message.answer(
                _welcome_msg(client.full_name, returning=True),
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                _welcome_msg(message.from_user.full_name, returning=False),
                parse_mode="HTML",
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
                _contact_linked_msg(client.full_name, phone),
                parse_mode="HTML",
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
                _contact_new_msg(),
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )


@router.message(F.text == "🔧 Записаться (⚠️ нужен HTTPS)")
async def need_https_handler(message: Message):
    await message.answer(
        "⚠️ <b>Telegram требует HTTPS</b> для Mini Apps.\n\n"
        "Для работы записи локально:\n"
        "1. Используйте туннель (<b>ngrok</b>)\n"
        "2. Укажите <code>https://...</code> в <code>.env</code>\n\n"
        "<i>Пока можете тестировать в браузере:</i>\n"
        "<code>http://localhost:5173/webapp</code>",
        parse_mode="HTML"
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
            await message.answer(
                "📱 Пожалуйста, сначала отправьте номер\n"
                "для регистрации.",
                parse_mode="HTML"
            )
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
            await message.answer(
                "📋 <b>Мои записи</b>\n\n"
                "<i>У вас пока нет активных записей.</i>\n\n"
                "Нажмите <b>🔧 Записаться на сервис</b>,\n"
                "чтобы выбрать услугу и время.",
                parse_mode="HTML"
            )
            return

        # Header
        await message.answer(
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 <b>Ваши записи</b>  ({len(appointments)})\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML"
        )

        # Each appointment as a card
        for appt in appointments:
            text = _appointment_card(appt)
            keyboard = get_appointment_keyboard(appt.id)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("cancel_appt:"))
async def cancel_appointment_handler(callback_query: Message):
    appt_id = int(callback_query.data.split(":")[1])
    async with async_session_local() as db:
        appt = await db.get(Appointment, appt_id)
        if appt:
            appt.status = AppointmentStatus.CANCELLED
            await db.commit()
            await callback_query.message.edit_text(
                f"❌ <b>Запись #{appt_id} отменена</b>\n\n"
                f"<i>Вы можете создать новую запись\n"
                f"в любое время.</i>",
                parse_mode="HTML"
            )

            # Broadcast update to dashboard
            redis = RedisService.get_redis()
            msg = {
                "type": "STATUS_UPDATE",
                "data": {
                    "id": appt.id,
                    "shop_id": appt.shop_id,
                    "status": "cancelled"
                }
            }
            await redis.publish("appointments_updates", json.dumps(msg))
        else:
            await callback_query.answer("Запись не найдена.")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback_query: Message):
    await callback_query.message.answer(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await callback_query.answer()


@router.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        service_id = data.get("service_id")
        date_str = data.get("date")
        appointment_id = data.get("appointment_id")
        is_waitlist = data.get("is_waitlist", False)

        if not service_id or not date_str:
            await message.answer(
                "⚠️ <b>Ошибка</b>\n\nНекорректные данные от приложения.",
                parse_mode="HTML"
            )
            return

        start_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        start_time_naive = start_time.replace(tzinfo=None)

        async with async_session_local() as db:
            service = await db.get(Service, service_id)
            if not service:
                await message.answer(
                    "⚠️ <b>Ошибка</b>\n\nУслуга не найдена.",
                    parse_mode="HTML"
                )
                return

            # Check for existing appointment if rescheduling
            existing_appt = None
            if appointment_id:
                existing_appt = await db.get(Appointment, int(appointment_id))
                if not existing_appt:
                    await message.answer(
                        "⚠️ <b>Ошибка</b>\n\nИсходная запись не найдена.",
                        parse_mode="HTML"
                    )
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
                    await message.answer(
                        "⏰ <b>Время занято</b>\n\n"
                        "Это время уже занято.\n"
                        "Пожалуйста, выберите другое.",
                        parse_mode="HTML"
                    )
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

            # Mark as UTC-aware so asyncpg doesn't convert from local timezone
            start_time_utc = start_time_naive.replace(tzinfo=tz.utc)
            end_time_utc = end_time.replace(tzinfo=tz.utc)

            status = AppointmentStatus.WAITLIST if is_waitlist else (
                AppointmentStatus.CONFIRMED if appointment_id else AppointmentStatus.NEW
            )

            if appointment_id:
                existing_appt.service_id = service_id
                existing_appt.start_time = start_time_utc
                existing_appt.end_time = end_time_utc
                existing_appt.status = status
                appt = existing_appt
            else:
                new_appt = Appointment(
                    shop_id=1,
                    client_id=client.id,
                    service_id=service_id,
                    start_time=start_time_utc,
                    end_time=end_time_utc,
                    status=status
                )
                db.add(new_appt)
                appt = new_appt

            await db.commit()
            await db.refresh(appt)

            if is_waitlist:
                msg = _waitlist_msg(
                    service.name,
                    start_time_naive.strftime('%d.%m.%Y')
                )
            else:
                msg = _booking_confirmed_msg(
                    service.name,
                    start_time_naive.strftime('%d.%m.%Y  %H:%M'),
                    is_edit=bool(appointment_id)
                )

            await message.answer(msg, parse_mode="HTML")

            try:
                redis = RedisService.get_redis()
                event_type = "WAITLIST_ADD" if is_waitlist else (
                    "APPOINTMENT_UPDATED" if appointment_id else "NEW_APPOINTMENT"
                )
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
        await message.answer(
            "⚠️ <b>Произошла ошибка</b>\n\n"
            "Пожалуйста, попробуйте ещё раз.",
            parse_mode="HTML"
        )


@router.message(F.text == "💬 Консультация")
async def consultation_button_handler(message: Message):
    await message.answer(
        "💬 <b>Консультация</b>\n\n"
        "Задайте ваш вопрос — я передам его мастеру\n"
        "и постараюсь ответить сразу.\n\n"
        "<i>Просто напишите свой вопрос в чат.</i>",
        parse_mode="HTML"
    )


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

            # 4. Reply with branded formatting
            await message.answer(
                f"💬 <b>Ответ мастера</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{response}",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
