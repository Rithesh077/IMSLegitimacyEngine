from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class Company(Base):
    __tablename__ = "corporate_profiles"

    id = Column(String, primary_key=True) # uuid
    company_name = Column(String)
    
    # verification details
    verification_status = Column(String, default="Unverified")
    ai_trust_score = Column(Float, default=0.0)
    ai_trust_tier = Column(String)
    rejection_reason = Column(String, nullable=True)
    ai_report_path = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    
    # contact/metadata
    hr_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    
    # business details
    cin = Column(String, nullable=True)
    company_type = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    registered_address = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # foreign key
    user_id = Column(String, nullable=False) # to user(id)
