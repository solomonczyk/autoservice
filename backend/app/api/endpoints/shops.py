from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Shop, User, UserRole
from app.api import deps
from pydantic import BaseModel

router = APIRouter()

class ShopCreate(BaseModel):
    name: str
    address: str

class ShopRead(ShopCreate):
    id: int
    class Config:
        from_attributes = True

@router.post("/", response_model=ShopRead)
async def create_shop(
    shop: ShopCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role([UserRole.ADMIN]))
):
    db_shop = Shop(name=shop.name, address=shop.address)
    db.add(db_shop)
    await db.commit()
    await db.refresh(db_shop)
    return db_shop

@router.get("/", response_model=List[ShopRead])
async def read_shops(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).offset(skip).limit(limit))
    shops = result.scalars().all()
    return shops
