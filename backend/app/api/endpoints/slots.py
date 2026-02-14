from datetime import date, datetime
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.slots import get_available_slots

router = APIRouter()

@router.get("/available", response_model=List[datetime])
async def get_slots(
    shop_id: int,
    service_duration: int,
    target_date: date = Query(..., description="Date to check for slots (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a list of available start times for a given shop and duration on a specific date.
    """
    return await get_available_slots(shop_id, service_duration, target_date, db)
