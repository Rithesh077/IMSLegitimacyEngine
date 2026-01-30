from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from prisma.models import User
from prisma.enums import Role, InternshipStatus
from app.db import db
from app.auth.dependencies import require_role, get_current_user
from app.internships.schemas import InternshipCreate, InternshipResponse

router = APIRouter(prefix="/internships", tags=["Internships"])

@router.post("", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
async def create_internship(
    data: InternshipCreate,
    current_user: User = Depends(require_role(Role.CORPORATE))
):
    # Ensure corporate profile exists
    corporate_profile = await db.corporateprofile.find_unique(where={"user_id": current_user.id})
    if not corporate_profile:
        # Should not happen if registered correctly, but safeguard
        raise HTTPException(status_code=400, detail="Corporate profile not found")

    # Verify session exists
    session = await db.internshipsession.find_unique(where={"id": data.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    internship = await db.internship.create(
        data={
            "title": data.title,
            "description": data.description,
            "status": InternshipStatus.PENDING, # Prompt says 'Corporate creates...' logic implies Pending or Draft. Placement views PENDING. So Pending makes sense.
            "session_id": data.session_id,
            "corporate_id": corporate_profile.id,
            "creator_id": current_user.id
        }
    )
    return internship

@router.get("/my", response_model=List[InternshipResponse])
async def list_my_internships(
    current_user: User = Depends(require_role(Role.CORPORATE))
):
    corporate_profile = await db.corporateprofile.find_unique(where={"user_id": current_user.id})
    if not corporate_profile:
         raise HTTPException(status_code=400, detail="Corporate profile not found")
         
    internships = await db.internship.find_many(
        where={"corporate_id": corporate_profile.id},
        order={"created_at": "desc"}
    )
    return internships

@router.get("/approved", response_model=List[InternshipResponse])
async def list_approved_internships(
    current_user: User = Depends(require_role(Role.STUDENT))
):
    internships = await db.internship.find_many(
        where={"status": InternshipStatus.APPROVED},
        order={"created_at": "desc"}
    )
    return internships
