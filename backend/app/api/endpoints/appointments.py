from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Appointment, Client, Service
from pydantic import BaseModel, root_validator

router = APIRouter()

class AppointmentCreate(BaseModel):
    shop_id: int
    service_id: int
    start_time: datetime
    # client info (simplified for MVP: creating client on fly or linking)
    client_name: str
    client_phone: str
    client_telegram_id: int = None

class AppointmentRead(BaseModel):
    id: int
    shop_id: int
    service_id: int
    client_id: int
    start_time: datetime
    end_time: datetime
    status: str
    
    class Config:
        from_attributes = True

@router.post("/", response_model=AppointmentRead)
async def create_appointment(
    appt: AppointmentCreate, 
    db: AsyncSession = Depends(get_db)
):
    # 1. Get Service to calculate duration
    service = await db.get(Service, appt.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # 2. Find or Create Client
    # Check if client exists by phone
    stmt = select(Client).where(Client.phone == appt.client_phone)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    
    if not client:
        client = Client(
            full_name=appt.client_name,
            phone=appt.client_phone,
            telegram_id=appt.client_telegram_id
        )
        db.add(client)
        await db.flush() # get ID
    
    # 3. Calculate End Time
    from datetime import timedelta
    end_time = appt.start_time + timedelta(minutes=service.duration_minutes)
    
    # 4. Create Appointment
    # TODO: Add locking here (Redis) to prevent race conditions
    
    new_appt = Appointment(
        shop_id=appt.shop_id,
        service_id=appt.service_id,
        client_id=client.id,
        start_time=appt.start_time,
        end_time=end_time,
        status="pending"
    )
    
    db.add(new_appt)
    await db.commit()
    await db.refresh(new_appt)
    return new_appt

@router.get("/", response_model=List[AppointmentRead])
async def read_appointments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).offset(skip).limit(limit))
    appts = result.scalars().all()
    return appts
