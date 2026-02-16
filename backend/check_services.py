import asyncio
from app.db.session import async_session_local
from app.models.models import Service
from sqlalchemy import select

async def main():
    async with async_session_local() as db:
        result = await db.execute(select(Service))
        services = result.scalars().all()
        
        print(f"Found {len(services)} services.")
        
        if not services:
            print("Creating default services...")
            s1 = Service(name="Dagnostics", duration_minutes=30, base_price=1500.0)
            s2 = Service(name="Oil Change", duration_minutes=45, base_price=2500.0)
            s3 = Service(name="Brake Replacement", duration_minutes=90, base_price=5000.0)
            
            db.add_all([s1, s2, s3])
            await db.commit()
            print("Services created!")
        else:
            for s in services:
                print(f"- {s.name} ({s.duration_minutes} min) - {s.base_price}")

if __name__ == "__main__":
    asyncio.run(main())
