from datetime import date
from pydantic import BaseModel
from typing import List

class SessionCreate(BaseModel):
    program: str
    batch: str
    academic_year: str
    start_date: date
    end_date: date

class SessionResponse(SessionCreate):
    id: str
    created_by_id: str
    
    class Config:
        from_attributes = True
