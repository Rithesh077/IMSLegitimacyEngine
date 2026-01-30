from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from prisma.models import User
from prisma.enums import Role, InternshipStatus
from app.db import db
from app.auth.dependencies import require_role
from app.internships.schemas import InternshipResponse
from app.approvals.utils import trigger_erp_sync

router = APIRouter(prefix="/internships", tags=["Placement"])

@router.get("/pending", response_model=List[InternshipResponse])
async def list_pending_internships(
    current_user: User = Depends(require_role(Role.PLACEMENT))
):
    internships = await db.internship.find_many(
        where={"status": InternshipStatus.PENDING},
        order={"created_at": "asc"}
    )
    return internships

@router.post("/{id}/approve", response_model=InternshipResponse)
async def approve_internship(
    id: str,
    current_user: User = Depends(require_role(Role.PLACEMENT))
):
    internship = await db.internship.find_unique(where={"id": id})
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    updated_internship = await db.internship.update(
        where={"id": id},
        data={"status": InternshipStatus.APPROVED}
    )
    
    # Trigger Mock ERP
    trigger_erp_sync(id)
    
    return updated_internship

@router.post("/{id}/reject", response_model=InternshipResponse)
async def reject_internship(
    id: str,
    current_user: User = Depends(require_role(Role.PLACEMENT))
):
    internship = await db.internship.find_unique(where={"id": id})
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
        
    updated_internship = await db.internship.update(
        where={"id": id},
        data={"status": InternshipStatus.REJECTED}
    )
    return updated_internship
