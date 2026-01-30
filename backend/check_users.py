import asyncio
from app.db import db

async def check_users():
    await db.connect()
    users = await db.user.find_many()
    print(f"Total Users Found: {len(users)}")
    for u in users:
        print(f"User: {u.email} | Role: {u.role}")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_users())
