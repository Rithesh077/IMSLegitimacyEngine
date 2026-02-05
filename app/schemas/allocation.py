from pydantic import BaseModel, Field
from typing import List, Optional

class FacultyProfile(BaseModel):
    id: str
    name: str
    department: str
    expertise: List[str]

class StudentProfile(BaseModel):
    id: str
    name: str
    internship_role: str
    internship_description: str  # Critical for matching
    skills: List[str] = []

class AllocationRequest(BaseModel):
    student: StudentProfile
    available_faculty: List[FacultyProfile]

class AllocationResponse(BaseModel):
    recommended_faculty_id: str
    faculty_name: str
    confidence_score: float
    reasoning: str
    is_random_fallback: bool
