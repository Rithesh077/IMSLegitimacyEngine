from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

# existing table
class User(Base):
    __tablename__ = "User" # case sensitive

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String) # student or faculty
    
    # relationships to allocation
    allocations_as_student = relationship("Allocation", foreign_keys="[Allocation.student_id]", back_populates="student")
    allocations_as_faculty = relationship("Allocation", foreign_keys="[Allocation.faculty_id]", back_populates="faculty")

# new table
class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    
    student_id = Column(String, ForeignKey("User.id"), unique=True)
    faculty_id = Column(String, ForeignKey("User.id"))
    
    confidence_score = Column(Float)
    reasoning = Column(String)
    is_random_fallback = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("User", foreign_keys=[student_id], back_populates="allocations_as_student")
    faculty = relationship("User", foreign_keys=[faculty_id], back_populates="allocations_as_faculty")
