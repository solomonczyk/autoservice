from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Service
from pydantic import BaseModel

router = APIRouter()

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    base_price: float

class ServiceRead(ServiceCreate):
    id: int
    class Config:
        from_attributes = True

@router.post("/", response_model=ServiceRead)
async def create_service(service: ServiceCreate, db: AsyncSession = Depends(get_db)):
    db_service = Service(
        name=service.name, 
        duration_minutes=service.duration_minutes,
        base_price=service.base_price
    )
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    return db_service

@router.get("/", response_model=List[ServiceRead])
async def read_services(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).offset(skip).limit(limit))
    services = result.scalars().all()
    return services
