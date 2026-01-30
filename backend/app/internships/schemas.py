from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from prisma.enums import InternshipStatus

class InternshipCreate(BaseModel):
    title: str
    description: str
    session_id: str

class InternshipResponse(BaseModel):
    id: str
    title: str
    description: str
    status: InternshipStatus
    created_at: datetime
    corporate_id: str
    session_id: str
    
    class Config:
        from_attributes = True
