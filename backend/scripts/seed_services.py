import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.db.session import async_session_local
from app.models.models import Service
from sqlalchemy import select

POPULAR_SERVICES = [
    {"name": "Замена масла и фильтра", "duration": 45, "price": 1500.0},
    {"name": "Диагностика ходовой", "duration": 30, "price": 1000.0},
    {"name": "Замена тормозных колодок", "duration": 60, "price": 2500.0},
    {"name": "Компьютерная диагностика", "duration": 30, "price": 1200.0},
    {"name": "Шиномонтаж (комплекс)", "duration": 60, "price": 3000.0},
    {"name": "Развал-схождение", "duration": 45, "price": 2000.0},
    {"name": "Замена свечей зажигания", "duration": 45, "price": 1500.0},
    {"name": "Заправка кондиционера", "duration": 40, "price": 2500.0},
    {"name": "Замена ремня ГРМ", "duration": 180, "price": 8000.0},
    {"name": "Промывка инжектора", "duration": 60, "price": 3500.0},
]

async def seed():
    try:
        async with async_session_local() as db:
            print("Checking existing services...")
            result = await db.execute(select(Service))
            existing = result.scalars().all()
            existing_names = {s.name for s in existing}
            
            to_add = []
            for svc in POPULAR_SERVICES:
                if svc["name"] not in existing_names:
                    new_service = Service(
                        name=svc["name"],
                        duration_minutes=svc["duration"],
                        base_price=svc["price"]
                    )
                    to_add.append(new_service)
            
            if to_add:
                print(f"Adding {len(to_add)} new services...")
                db.add_all(to_add)
                await db.commit()
                print("Done!")
            else:
                print("All services already exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
