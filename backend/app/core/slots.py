from datetime import datetime, timedelta, time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.models import Appointment, Shop
from app.db.session import get_db

# Configuration for working hours (could be moved to DB/Config)
WORK_START = time(9, 0)
WORK_END = time(18, 0)

async def get_available_slots(
    shop_id: int,
    service_duration_minutes: int,
    date: datetime.date,
    db: AsyncSession
) -> List[datetime]:
    """
    Generates available time slots for a specific date and service duration.
    """
    
    # 1. Define working window for the day
    start_datetime = datetime.combine(date, WORK_START)
    end_datetime = datetime.combine(date, WORK_END)
    
    # 2. Fetch existing appointments for the shop on that day
    # We grab any appointment that overlaps with the day
    stmt = select(Appointment).where(
        and_(
            Appointment.shop_id == shop_id,
            Appointment.start_time >= start_datetime,
            Appointment.start_time < end_datetime,
            Appointment.status != 'cancelled'
        )
    ).order_by(Appointment.start_time)
    
    result = await db.execute(stmt)
    appointments = result.scalars().all()
    
    # 3. Generate slots
    slots = []
    current_time = start_datetime
    
    # Step size for slots (e.g., every 30 minutes, or rigid based on service duration)
    # Strategy: "Rigid blocks" - we check every X minutes if a service of duration Y fits.
    # Let's say we check every 30 mins.
    step_minutes = 30 
    
    while current_time + timedelta(minutes=service_duration_minutes) <= end_datetime:
        slot_end = current_time + timedelta(minutes=service_duration_minutes)
        is_free = True
        
        # Check collision with existing appointments
        for appt in appointments:
            # Check overlap
            # Overlap if (StartA < EndB) and (EndA > StartB)
            # Here A is the potential slot, B is the existing appointment
            # Appt times are timezone aware in DB? Assuming naive for simplicity first, or matching TZs.
            # Using naive comparison if both are naive.
            
            # Make sure to handle TZ info correctly in production. 
            # Assuming DB returns naive or consistent UTC.
            appt_start = appt.start_time.replace(tzinfo=None)
            appt_end = appt.end_time.replace(tzinfo=None)
            
            if current_time < appt_end and slot_end > appt_start:
                is_free = False
                break
        
        if is_free:
            slots.append(current_time)
            
        current_time += timedelta(minutes=step_minutes)
        
    return slots
