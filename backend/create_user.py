import asyncio
from app.db.session import async_session_local
from app.models.models import User, Shop, UserRole
from app.core.security import get_password_hash

async def create_initial_data():
    async with async_session_local() as db:
        # 1. Create Shop
        shop = Shop(name="Best Auto", address="123 Main St")
        db.add(shop)
        await db.flush()
        
        # 2. Create User
        user = User(
            username="admin",
            hashed_password=get_password_hash("admin"),
            shop_id=shop.id,
            role=UserRole.ADMIN
        )
        db.add(user)
        await db.commit()
        print(f"Created user 'admin' with password 'admin' and role 'ADMIN' for shop '{shop.name}'")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(create_initial_data())
