import asyncio
import sys
import os
from datetime import date

# Add project root to path
sys.path.append("/app")

from app.db.session import async_session_local
from app.core.slots import get_available_slots

async def main():
    try:
        async with async_session_local() as db:
            print("Checking slots for 2026-02-18...")
            slots = await get_available_slots(
                shop_id=1,
                service_duration_minutes=30,
                date=date(2026, 2, 18),
                db=db
            )
            print(f"Slots found: {len(slots)}")
            for s in slots:
                print(s)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
