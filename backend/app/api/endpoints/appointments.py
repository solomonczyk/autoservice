from typing import List
from datetime import datetime, timedelta
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.api import deps
from app.models.models import Appointment, AppointmentStatus, Client, Service, User, UserRole
from app.services.redis_service import RedisService 
from pydantic import BaseModel, root_validator

router = APIRouter()

class AppointmentCreate(BaseModel):
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

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus

class AppointmentUpdate(BaseModel):
    service_id: int = None
    start_time: datetime = None

@router.patch("/{id}", response_model=AppointmentRead)
async def update_appointment(
    id: int,
    appt_update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    stmt = select(Appointment).where(Appointment.id == id)
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if appt.shop_id != current_user.shop_id:
         raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

    if appt_update.service_id:
        service = await db.get(Service, appt_update.service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        appt.service_id = appt_update.service_id
        # Trigger recalculation of end_time if start_time or service changed
        start = appt_update.start_time or appt.start_time
        appt.end_time = start + timedelta(minutes=service.duration_minutes)
        
    if appt_update.start_time:
        appt.start_time = appt_update.start_time
        # Ensure end_time stays in sync with duration
        service = await db.get(Service, appt.service_id)
        appt.end_time = appt.start_time + timedelta(minutes=service.duration_minutes)

    await db.commit()
    await db.refresh(appt)
    
    # Broadcast update
    redis = RedisService.get_redis()
    message = {
        "type": "APPOINTMENT_UPDATED",
        "data": {
            "id": appt.id,
            "shop_id": appt.shop_id
        }
    }
    await redis.publish("appointments_updates", json.dumps(message))
    
    return appt

@router.post("/", response_model=AppointmentRead)
async def create_appointment(
    appt: AppointmentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    # 0. Enforce Tenancy
    shop_id = current_user.shop_id

    # 1. Get Service to calculate duration
    service = await db.get(Service, appt.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # Calculate end_time based on service duration
    end_time = appt.start_time + timedelta(minutes=service.duration_minutes)

    # 2. Race Condition Protection (Soft Lock)
    redis = RedisService.get_redis()
    lock_key = f"booking_lock:{shop_id}:{appt.start_time.isoformat()}"
    
    is_locked = await redis.set(lock_key, "1", nx=True, ex=10)
    if not is_locked:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot is currently being booked by someone else. Please try again."
        )

    try:
        stmt = select(Appointment).where(
            and_(
                Appointment.shop_id == shop_id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.start_time < end_time,
                Appointment.end_time > appt.start_time
            )
        )
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slot already taken"
            )

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
            await db.flush()
        
        new_appt = Appointment(
            shop_id=shop_id,
            service_id=appt.service_id,
            client_id=client.id,
            start_time=appt.start_time,
            end_time=end_time,
            status=AppointmentStatus.NEW
        )
        
        db.add(new_appt)
        await db.commit()
        await db.refresh(new_appt)
        
        message = {
            "type": "NEW_APPOINTMENT",
            "data": {
                "id": new_appt.id,
                "shop_id": new_appt.shop_id,
                "start_time": new_appt.start_time.isoformat()
            }
        }
        await redis.publish("appointments_updates", json.dumps(message))
        
        return new_appt
        
    finally:
        await redis.delete(lock_key)

@router.patch("/{id}/status", response_model=AppointmentRead)
async def update_appointment_status(
    id: int,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    from sqlalchemy.orm import joinedload
    stmt = select(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.service)
    ).where(Appointment.id == id)
    
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if appt.shop_id != current_user.shop_id:
         raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

    old_status = appt.status
    appt.status = status_update.status
    
    await db.commit()
    await db.refresh(appt)
    
    if appt.status != old_status and appt.client.telegram_id:
        from app.services.notification_service import NotificationService
        import asyncio
        asyncio.create_task(
            NotificationService.notify_client_status_change(
                chat_id=appt.client.telegram_id,
                service_name=appt.service.name,
                new_status=appt.status.value
            )
        )
        
    redis = RedisService.get_redis()
    message = {
        "type": "STATUS_UPDATE",
        "data": {
            "id": appt.id,
            "shop_id": appt.shop_id,
            "status": appt.status.value
        }
    }
    await redis.publish("appointments_updates", json.dumps(message))
    
    return appt

@router.get("/", response_model=List[AppointmentRead])
async def read_appointments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{id}", response_model=AppointmentRead)
async def read_appointment(
    id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get appointment by ID. 
    Publicly accessible (for now) to allow WebApp to fetch details without login.
    In production, this should ideally use a signed token or similar.
    """
    appt = await db.get(Appointment, id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt
