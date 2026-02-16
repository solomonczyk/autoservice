import asyncio
import csv
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_local
from app.models.models import Client
from sqlalchemy import select

async def import_clients(csv_file: str):
    print(f"Starting import from {csv_file}...")
    
    count = 0
    async with async_session_local() as db:
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                full_name = row.get('full_name')
                phone = row.get('phone', '').replace('+', '').strip()
                vehicle_info = row.get('vehicle_info')
                
                if not phone:
                    continue
                
                # Check for duplicates
                stmt = select(Client).where(Client.phone == phone)
                result = await db.execute(stmt)
                if result.scalar_one_or_none():
                    print(f"Skipping duplicate: {phone}")
                    continue
                
                client = Client(
                    full_name=full_name,
                    phone=phone,
                    vehicle_info=vehicle_info
                )
                db.add(client)
                count += 1
                
        await db.commit()
    
    print(f"Successfully imported {count} clients!")

if __name__ == "__main__":
    file_path = "clients_sample.csv"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    asyncio.run(import_clients(file_path))
