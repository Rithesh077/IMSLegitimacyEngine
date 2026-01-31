from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List, Optional
import shutil
import uuid
import os
from prisma.models import User
from prisma.enums import Role, InternshipStatus
from app.db import db
from app.auth.dependencies import require_role, get_current_user
from app.internships.schemas import InternshipCreate, InternshipResponse, InternshipUpdate, ApplicationCreate, ApplicationResponse
from app.services.file_storage import get_storage_service

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

@router.get("/approved")
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
    
    # For students, check which internships they've already applied to
    if current_user.role == Role.STUDENT:
        student_applications = await db.application.find_many(
            where={"student_id": current_user.id}
        )
        applied_internship_ids = {app.internship_id for app in student_applications}
        
        result = []
        for internship in internships:
            internship_dict = {
                "id": internship.id,
                "title": internship.title,
                "description": internship.description,
                "status": internship.status,
                "department": {
                    "id": internship.department.id,
                    "name": internship.department.name
                },
                "location_type": internship.location_type,
                "is_paid": internship.is_paid,
                "stipend": internship.stipend,
                "duration": internship.duration,
                "created_at": internship.created_at.isoformat(),
                "corporate_id": internship.corporate_id,
                "has_applied": internship.id in applied_internship_ids
            }
            result.append(internship_dict)
        return result
    else:
        # For placement officers, return regular response
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

@router.post("/{internship_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_internship(
    internship_id: str,
    resume: UploadFile = File(...),
    github_link: Optional[str] = Form(None),
    linkedin_link: Optional[str] = Form(None),
    current_user: User = Depends(require_role(Role.STUDENT))
):
    # Check if internship exists and is approved
    internship = await db.internship.find_unique(where={"id": internship_id})
    if not internship or internship.status != InternshipStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Internship not found or not open for applications")

    # Check if already applied
    existing_application = await db.application.find_first(
        where={
            "internship_id": internship_id,
            "student_id": current_user.id
        }
    )
    if existing_application:
        raise HTTPException(status_code=400, detail="You have already applied for this internship")

    # Save Resume File (using Storage Service)
    file_extension = os.path.splitext(resume.filename)[1]
    unique_filename = f"{current_user.id}_{uuid.uuid4()}{file_extension}"
    
    # Delegate to storage service (Local or S3 based on env)
    file_url = await get_storage_service().save(resume, unique_filename)

    application = await db.application.create(
        data={
            "resume_link": file_url,
            "github_link": github_link,
            "linkedin_link": linkedin_link,
            "internship_id": internship_id,
            "student_id": current_user.id
        },
        include={"student": True}
    )
    return application

@router.get("/{internship_id}/applications", response_model=List[ApplicationResponse])
async def get_internship_applications(
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
        raise HTTPException(status_code=403, detail="Not authorized to view applications for this internship")

    applications = await db.application.find_many(
        where={"internship_id": internship_id},
        include={"student": True},
        order={"created_at": "desc"}
    )
    return applications
