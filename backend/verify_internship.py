import asyncio
import httpx
from app.db import db

BASE_URL = "http://localhost:8000"

async def verify():
    # helper to clean up
    print("Connecting to DB...")
    await db.connect()
    
    email = "testcorp@example.com"
    password = "password123"
    
    # clean up existing user if any
    existing_user = await db.user.find_unique(where={"email": email})
    if existing_user:
        # delete related profile first because cascade might not be set up for profile user relation deletion automatically
        # schema has relations so lets just try deleting user
        # or wait we might have foreign key constraints
        # lets delete internships first
        try:
             profile = await db.corporateprofile.find_unique(where={"user_id": existing_user.id})
             if profile:
                 await db.internship.delete_many(where={"corporate_id": profile.id})
                 await db.corporateprofile.delete(where={"id": profile.id})
             await db.user.delete(where={"id": existing_user.id})
        except Exception as e:
            print(f"Cleanup error: {e}")

    # registering corporate user
    print("Registering User...")
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        reg_res = await client.post("/auth/register", json={
            "name": "Test Corp User",
            "email": email,
            "password": password,
            "company_name": "Test Company",
            "hr_name": "Test HR"
        })
        if reg_res.status_code != 201:
            print(f"Registration failed: {reg_res.text}")
            return

        # logging in
        print("Logging in...")
        login_res = await client.post("/auth/login", data={
            "username": email,
            "password": password
        })
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # create corporate profile
        # this is handled by registration

        # posting internship
        print("Fetching Departments...")
        dept_res = await client.get("/departments")
        if dept_res.status_code != 200:
             print("Failed to fetch departments")
             return
        departments = dept_res.json()
        if not departments:
             print("No departments found")
             return
        dept_id = departments[0]['id']

        print("Posting Internship...")
        internship_data = {
            "title": "Software Intern",
            "description": "Python dev",
            "department_id": dept_id,
            "location_type": "REMOTE",
            "is_paid": True,
            "stipend": "50000",
            "duration": "6 months"
        }
        
        post_res = await client.post("/internships", json=internship_data, headers=headers)
        if post_res.status_code == 201:
            print("Internship Created Successfully!")
            print(post_res.json())
        else:
            print(f"Failed to create internship: {post_res.status_code} - {post_res.text}")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(verify())
