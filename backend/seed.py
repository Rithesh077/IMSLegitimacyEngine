import asyncio
from prisma.enums import Role
from app.db import db
from app.utils.security import get_password_hash

async def main():
    await db.connect()
    
    password = get_password_hash("password123")
    
    # Create Faculty
    faculty = await db.user.upsert(
        where={"email": "faculty@example.com"},
        data={
            "create": {
                "name": "Faculty Member",
                "email": "faculty@example.com",
                "password": password,
                "role": Role.FACULTY
            },
            "update": {}
        }
    )
    print(f"Created Faculty: {faculty.email}")

    # Create Placement
    placement = await db.user.upsert(
        where={"email": "placement@example.com"},
        data={
            "create": {
                "name": "Placement Officer",
                "email": "placement@example.com",
                "password": password,
                "role": Role.PLACEMENT
            },
            "update": {}
        }
    )
    print(f"Created Placement: {placement.email}")

    # Create Student
    student = await db.user.upsert(
        where={"email": "student@example.com"},
        data={
            "create": {
                "name": "Student User",
                "email": "student@example.com",
                "password": password,
                "role": Role.STUDENT
            },
            "update": {}
        }
    )
    print(f"Created Student: {student.email}")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
