from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api import deps
from app.models.models import Client, User, UserRole
from pydantic import BaseModel

router = APIRouter()

class ClientOut(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    phone: str
    vehicle_info: str | None = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ClientOut])
async def read_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve clients.
    """
    # Only allow staff/admin/manager to see clients
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF]:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    stmt = select(Client).offset(skip).limit(limit)
    result = await db.execute(stmt)
    clients = result.scalars().all()
    return clients
