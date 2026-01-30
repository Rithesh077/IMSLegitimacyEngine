from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from prisma.models import User
from prisma.enums import Role, InternshipStatus
from app.db import db
from app.auth.dependencies import require_role, get_current_user
from app.internships.schemas import InternshipCreate, InternshipResponse, InternshipUpdate

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

    internship = await db.internship.create(
        data={
            "title": data.title,
            "description": data.description,
            "status": InternshipStatus.PENDING, 
            "department_id": data.department_id,
            "location_type": data.location_type,
            "is_paid": data.is_paid,
            "stipend": data.stipend,
            "duration": data.duration,
            "corporate_id": corporate_profile.id,
            "creator_id": current_user.id
        },
        include={"department": True}
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
        order={"created_at": "desc"},
        include={"department": True}
    )
    return internships

@router.get("/approved", response_model=List[InternshipResponse])
async def list_approved_internships(
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [Role.STUDENT, Role.PLACEMENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Required role: STUDENT or PLACEMENT"
        )
        
    internships = await db.internship.find_many(
        where={"status": InternshipStatus.APPROVED},
        order={"created_at": "desc"},
        include={"department": True}
    )
    return internships

@router.patch("/{internship_id}/close")
async def close_internship(
    internship_id: str,
    current_user: User = Depends(get_current_user)
):
    """Close an internship (mark as CLOSED without deleting)"""
    internship = await db.internship.find_unique(where={"id": internship_id})
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    if current_user.role == Role.CORPORATE:
        # Corporate users can only close their own internships
        corporate_profile = await db.corporateprofile.find_unique(where={"user_id": current_user.id})
        if not corporate_profile or internship.corporate_id != corporate_profile.id:
             raise HTTPException(status_code=403, detail="Not authorized to close this internship")
             
    elif current_user.role != Role.PLACEMENT:
        # Only Corporate and Placement can close internships
        raise HTTPException(status_code=403, detail="Operation not permitted")
    
    updated = await db.internship.update(
        where={"id": internship_id},
        data={"status": InternshipStatus.CLOSED}
    )
    return updated

@router.delete("/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_internship(
    internship_id: str,
    current_user: User = Depends(require_role(Role.CORPORATE))
):
    corporate_profile = await db.corporateprofile.find_unique(where={"user_id": current_user.id})
    if not corporate_profile:
        raise HTTPException(status_code=400, detail="Corporate profile not found")
    
    internship = await db.internship.find_unique(where={"id": internship_id})
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    if internship.corporate_id != corporate_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this internship")
        
    await db.internship.delete(where={"id": internship_id})
    return None

@router.patch("/{id}", response_model=InternshipResponse)
async def update_internship(
    id: str,
    data: InternshipUpdate,
    current_user: User = Depends(require_role(Role.CORPORATE))
):
    corporate_profile = await db.corporateprofile.find_unique(where={"user_id": current_user.id})
    if not corporate_profile:
        raise HTTPException(status_code=400, detail="Corporate profile not found")
        
    internship = await db.internship.find_unique(where={"id": id})
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    if internship.corporate_id != corporate_profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this internship")
    
    update_data = data.dict(exclude_unset=True)
    
    updated_internship = await db.internship.update(
        where={"id": id},
        data=update_data,
        include={"department": True}
    )
    return updated_internship
