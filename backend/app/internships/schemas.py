from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from prisma.enums import InternshipStatus, LocationType

class InternshipCreate(BaseModel):
    title: str
    description: str
    department_id: str
    location_type: LocationType
    is_paid: bool
    stipend: Optional[str] = None
    duration: str

class InternshipUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[str] = None
    location_type: Optional[LocationType] = None
    is_paid: Optional[bool] = None
    stipend: Optional[str] = None
    duration: Optional[str] = None

class Department(BaseModel):
    id: str
    name: str

class InternshipResponse(BaseModel):
    id: str
    title: str
    description: str
    status: InternshipStatus
    department: Department
    location_type: LocationType
    is_paid: bool
    stipend: Optional[str] = None
    duration: str
    created_at: datetime
    corporate_id: str
    
    class Config:
        from_attributes = True
