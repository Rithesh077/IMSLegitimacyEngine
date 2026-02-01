from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from prisma.models import User
from prisma.enums import Role
from app.db import db
from app.auth.dependencies import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
async def list_users(
    current_user: User = Depends(require_role(Role.ADMIN))
):
    users = await db.user.find_many(
        order={"created_at": "desc"},
        include={"corporate_profile": True}
    )
    return users

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(require_role(Role.ADMIN))
):
    total_users = await db.user.count()
    total_internships = await db.internship.count()
    corporate_count = await db.corporateprofile.count()
    
    # Chart Data: Users by Role
    # Using explicit aggregation or group_by if available. 
    # Fallback to simple iteration for safety with Enums
    users_by_role = {}
    for role in Role:
        count = await db.user.count(where={"role": role})
        if count > 0:
            users_by_role[role.value] = count
            
    # Chart Data: Internships by Status
    from prisma.enums import InternshipStatus
    internships_by_status = {}
    for status in InternshipStatus:
        count = await db.internship.count(where={"status": status})
        if count > 0:
            internships_by_status[status.value] = count
            
    # Chart Data: Internships by Department
    # Fetch departments with internship counts
    departments = await db.department.find_many(
        include={
            "internships": True # We can just count the list length
        }
    )
    internships_by_dept = {d.name: len(d.internships) for d in departments if d.internships}

    return {
        "total_users": total_users,
        "total_internships": total_internships,
        "corporate_count": corporate_count,
        "charts": {
            "users_by_role": users_by_role,
            "internships_by_status": internships_by_status,
            "internships_by_dept": internships_by_dept
        }
    }

@router.delete("/users/{id}")
async def delete_user(
    id: str,
    current_user: User = Depends(require_role(Role.ADMIN))
):
    # Prevent deleting self
    if id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Cascade delete is handled by database usually, but for Prisma we might need explicit handling
    # For now assuming Prisma handles it or we catch errors
    try:
        await db.user.delete(where={"id": id})
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User deleted"}

@router.get("/internships")
async def list_all_internships(
    current_user: User = Depends(require_role(Role.ADMIN))
):
    return await db.internship.find_many(
        order={"created_at": "desc"},
        include={"department": True, "corporate": True}
    )

@router.delete("/internships/{id}")
async def delete_internship(
    id: str,
    current_user: User = Depends(require_role(Role.ADMIN))
):
    await db.internship.delete(where={"id": id})
    return {"message": "Internship deleted"}

from pydantic import BaseModel
from typing import Optional
from app.utils.security import get_password_hash

class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Role
    # Optional fields for Corporate
    company_name: Optional[str] = None
    hr_name: Optional[str] = None

@router.post("/users")
async def create_user(
    data: AdminUserCreate,
    current_user: User = Depends(require_role(Role.ADMIN))
):
    # Check email
    existing = await db.user.find_unique(where={"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pw = get_password_hash(data.password)
    
    # Prepare create data
    create_data = {
        "name": data.name,
        "email": data.email,
        "password": hashed_pw,
        "role": data.role
    }
    
    # Handle Corporate Profile
    if data.role == Role.CORPORATE:
        if not data.company_name:
            raise HTTPException(status_code=400, detail="Company Name is required for Corporate role")
        create_data["corporate_profile"] = {
            "create": {
                "company_name": data.company_name,
                "hr_name": data.hr_name or data.name,
                "email": data.email
            }
        }
    
    user = await db.user.create(
        data=create_data,
        include={"corporate_profile": True} if data.role == Role.CORPORATE else None
    )
    return user

@router.get("/verifications/pending")
async def list_pending_verifications(
    current_user: User = Depends(require_role(Role.ADMIN))
):
    # fetch all corporate profiles
    # optimized: filtered in python for flexibilty (json handling)
    profiles = await db.corporateprofile.find_many(
        where={
            "verification_report": {"not": None} # only those with reports
        },
        include={"user": True}
    )
    
    pending = []
    for p in profiles:
        # check status in json
        if p.verification_report:
            # handle both dict and json string if prisma returns generic json
            report = p.verification_report
            
            # check unverified status
            # status could be 'Unverified' or 'Unknown' or low score
            status = report.get("status")
            if status == "Unverified" or status == "Unknown":
                pending.append({
                    "id": p.id,
                    "company_name": p.company_name,
                    "country": p.country,
                    "user_email": p.user.email,
                    "hr_name": p.hr_name,
                    "verification_report": report,
                    "registered_at": p.user.created_at
                })
                
    return pending
