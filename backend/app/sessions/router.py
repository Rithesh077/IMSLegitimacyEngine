from fastapi import APIRouter, Depends, status
from typing import List
from prisma.models import User
from prisma.enums import Role
from app.db import db
from app.auth.dependencies import require_role
from app.sessions.schemas import SessionCreate, SessionResponse

router = APIRouter(prefix="/sessions", tags=["Faculty"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(require_role(Role.FACULTY))
):
    # Convert date objects to datetime for Prisma if needed, but Prisma Python usually handles date objects for DateTime fields if defined as DateTime in schema.
    # Schema says DateTime. Passing date might work or need datetime conversion. 
    # Safest is datetime.
    from datetime import datetime
    
    session = await db.internshipsession.create(
        data={
            "program": data.program,
            "batch": data.batch,
            "academic_year": data.academic_year,
            "start_date": datetime.combine(data.start_date, datetime.min.time()),
            "end_date": datetime.combine(data.end_date, datetime.min.time()),
            "created_by_id": current_user.id
        }
    )
    return session

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(require_role(Role.FACULTY))
):
    sessions = await db.internshipsession.find_many(
        order={"start_date": "desc"}
    )
    return sessions
