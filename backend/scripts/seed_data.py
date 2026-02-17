import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))

from sqlalchemy import select
from app.db.session import async_session_local
from app.models.models import User, Shop, Service, UserRole
from app.core.security import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def seed_data():
    async with async_session_local() as db:
        try:
            # 1. Check/Create Shop
            logger.info("Checking Shop...")
            result = await db.execute(select(Shop).where(Shop.name == "Best Auto"))
            shop = result.scalar_one_or_none()
            
            if not shop:
                shop = Shop(name="Best Auto", address="123 Main St")
                db.add(shop)
                await db.flush()
                logger.info(f"Created Shop: {shop.name}")
            else:
                logger.info(f"Shop already exists: {shop.name}")

            # 2. Check/Create Admin User
            logger.info("Checking Admin User...")
            result = await db.execute(select(User).where(User.username == "admin"))
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    username="admin",
                    hashed_password=get_password_hash("admin"),
                    shop_id=shop.id,
                    role=UserRole.ADMIN
                )
                db.add(user)
                await db.flush()
                logger.info("Created Admin User")
            else:
                logger.info("Admin User already exists")

            # 3. Check/Create Services
            logger.info("Checking Services...")
            result = await db.execute(select(Service))
            existing_services = result.scalars().all()
            existing_names = {s.name for s in existing_services}
            
            new_services = []
            for svc in POPULAR_SERVICES:
                if svc["name"] not in existing_names:
                    new_service = Service(
                        name=svc["name"],
                        duration_minutes=svc["duration"],
                        base_price=svc["price"]
                    )
                    new_services.append(new_service)
            
            if new_services:
                db.add_all(new_services)
                logger.info(f"Adding {len(new_services)} new services...")
            else:
                logger.info("All popular services already exist.")

            await db.commit()
            logger.info("Seeding completed successfully!")

        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())
