from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CompanyInput(BaseModel):
    name: str
    country: str
    registry_id: str
    document_content: Optional[str] = None
    manual_verification: bool = False
    
    # New Signal Fields
    linkedin_url: Optional[str] = None
    website_urls: Optional[List[str]] = Field(default_factory=list)
    recruiter_website: Optional[str] = None # Keeping for backward compat or merge with website_urls

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
