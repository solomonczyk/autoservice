import pytest
from datetime import date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock
from app.core.slots import get_available_slots, WORK_START, WORK_END
from app.models.models import Appointment

@pytest.mark.asyncio
async def test_get_available_slots_empty_day():
    # Mock DB session
    db = AsyncMock()
    # Mock result of execute
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    db.execute.return_value = mock_result
    
    shop_id = 1
    duration = 60
    target_date = date(2026, 2, 20)
    
    slots = await get_available_slots(shop_id, duration, target_date, db)
    
    # Check if slots are generated across the whole working day
    # 9:00 to 18:00 (9 hours). With 60 min duration and 30 min step.
    # Slots: 9:00, 9:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00
    # Last slot starts at 17:00 and ends at 18:00.
    assert len(slots) > 0
    assert slots[0] == datetime.combine(target_date, WORK_START)
    assert slots[-1] == datetime.combine(target_date, WORK_END) - timedelta(minutes=duration)

@pytest.mark.asyncio
async def test_get_available_slots_with_appointment():
    # Mock DB session
    db = AsyncMock()
    
    target_date = date(2026, 2, 20)
    shop_id = 1
    
    # Existing appointment: 10:00 - 11:00
    appt = Appointment(
        shop_id=shop_id,
        start_time=datetime.combine(target_date, time(10, 0)),
        end_time=datetime.combine(target_date, time(11, 0)),
        status='confirmed'
    )
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [appt]
    db.execute.return_value = mock_result
    
    duration = 60
    slots = await get_available_slots(shop_id, duration, target_date, db)
    
    # Slot 9:00 should be free
    assert datetime.combine(target_date, time(9, 0)) in slots
    # Slot 9:30 should be blocked (because it ends at 10:30, overlapping with appt)
    assert datetime.combine(target_date, time(9, 30)) not in slots
    # Slot 10:00 should be blocked
    assert datetime.combine(target_date, time(10, 0)) not in slots
    # Slot 10:30 should be blocked
    assert datetime.combine(target_date, time(10, 30)) not in slots
    # Slot 11:00 should be free
    assert datetime.combine(target_date, time(11, 0)) in slots

@pytest.mark.asyncio
async def test_get_available_slots_full_day_blocked():
    db = AsyncMock()
    target_date = date(2026, 2, 20)
    
    # Appt covers entire working day
    appt = Appointment(
        shop_id=1,
        start_time=datetime.combine(target_date, WORK_START),
        end_time=datetime.combine(target_date, WORK_END),
        status='confirmed'
    )
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [appt]
    db.execute.return_value = mock_result
    
    slots = await get_available_slots(1, 60, target_date, db)
    assert len(slots) == 0
