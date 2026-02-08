from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CompanyInput(BaseModel):
    name: str
    country: str
    hr_name: str
    hr_email: str
    
    industry: Optional[str] = None
    registered_address: Optional[str] = None
    registry_id: Optional[str] = None
    document_content: Optional[str] = None
    manual_verification: bool = False
    
    # Optional Signals
    linkedin_url: Optional[str] = None
    website_urls: Optional[List[str]] = Field(default_factory=list)
    user_id: Optional[str] = None # Required for DB persistence

class VerificationResult(BaseModel):
    verified: bool
    confidence_score: float
    details: Dict[str, Any]

class CredibilityAnalysis(BaseModel):
    trust_score: float
    trust_tier: str
    verification_status: str
    review_count: int
    sentiment_summary: str
    scraped_sources: List[str]
    red_flags: List[str]
    details: Dict[str, Any]
