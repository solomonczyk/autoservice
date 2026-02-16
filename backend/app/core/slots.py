from datetime import datetime, timedelta, time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.models import Appointment, Shop, AppointmentStatus
from app.db.session import get_db

# Configuration for working hours (could be moved to DB/Config)
WORK_START = time(9, 0)
WORK_END = time(18, 0)

async def get_available_slots(
    shop_id: int,
    service_duration_minutes: int,
    date: datetime.date,
    db: AsyncSession,
    exclude_appointment_id: Optional[int] = None
) -> List[datetime]:
    """
    Generates available time slots for a specific date and service duration.
    """
    
    # 1. Define working window for the day
    start_datetime = datetime.combine(date, WORK_START)
    end_datetime = datetime.combine(date, WORK_END)
    
    # 2. Fetch existing appointments for the shop on that day
    filters = [
        Appointment.shop_id == shop_id,
        Appointment.start_time >= start_datetime,
        Appointment.start_time < end_datetime,
        Appointment.status != AppointmentStatus.CANCELLED,
        Appointment.status != AppointmentStatus.WAITLIST
    ]
    if exclude_appointment_id:
        filters.append(Appointment.id != exclude_appointment_id)

    stmt = select(Appointment).where(and_(*filters)).order_by(Appointment.start_time)
    
    result = await db.execute(stmt)
    appointments = result.scalars().all()
    
    # 3. Generate slots
    slots = []
    
    # If today, don't show past slots
    now = datetime.now()
    if date == now.date():
        # Start from the latest of (work start) or (now + buffer)
        # Round up to the next 30 min interval for clean UI
        start_search = max(start_datetime, now)
        minutes_to_next_slot = 30 - (start_search.minute % 30)
        current_time = (start_search + timedelta(minutes=minutes_to_next_slot)).replace(second=0, microsecond=0)
    else:
        current_time = start_datetime
    
    # Step size for slots
    step_minutes = 30 
    
    while current_time + timedelta(minutes=service_duration_minutes) <= end_datetime:
        slot_end = current_time + timedelta(minutes=service_duration_minutes)
        is_free = True
        
        # Check collision with existing appointments
        for appt in appointments:
            appt_start = appt.start_time.replace(tzinfo=None)
            appt_end = appt.end_time.replace(tzinfo=None)
            
            if current_time < appt_end and slot_end > appt_start:
                is_free = False
                break
        
        if is_free:
            slots.append(current_time)
            
        current_time += timedelta(minutes=step_minutes)
        
    return slots
