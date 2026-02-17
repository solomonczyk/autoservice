from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Service, User, UserRole
from app.api import deps
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
async def create_service(
    service: ServiceCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN]))
):
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

@router.put("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: int,
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service.name = service_in.name
    service.duration_minutes = service_in.duration_minutes
    service.base_price = service_in.base_price
    
    await db.commit()
    await db.refresh(service)
    return service

@router.delete("/{service_id}", response_model=ServiceRead)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN]))
):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await db.delete(service)
    await db.commit()
    return service
