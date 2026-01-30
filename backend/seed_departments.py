import asyncio
from app.db import db

async def seed_departments():
    await db.connect()
    departments = [
        "Computer Science",
        "Information Technology",
        "Electronics & Communication",
        "Electrical Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Business Administration",
        "Design"
    ]
    
    print("Seeding departments...")
    for dept in departments:
        existing = await db.department.find_unique(where={"name": dept})
        if not existing:
            await db.department.create(data={"name": dept})
            print(f"Created: {dept}")
        else:
            print(f"Exists: {dept}")
            
    print("Seeding complete.")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_departments())
