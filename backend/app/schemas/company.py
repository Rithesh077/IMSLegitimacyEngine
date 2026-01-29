from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CompanyInput(BaseModel):
    """
    input for the analysis endpoint
    """
    name: str = Field(..., description="the official name of the company")
    cin: Optional[str] = Field(None, description="cin (21 chars)")
    domain: Optional[str] = Field(None, description="company website")

class VerificationResult(BaseModel):
    """
    result of the registry check
    """
    is_registered: bool = False
    cin: Optional[str] = None
    registration_date: Optional[str] = None
    status: str = "Unknown"  # active, struck off, etc
    confidence_score: float = 0.0
    verification_source: str = "None"
    red_flags: List[str] = []
    
    # internal flag to control flow
    can_proceed_to_scraping: bool = False

class CredibilityAnalysis(BaseModel):
    """
    final output for frontend
    """
    trust_score: float = Field(..., ge=0, le=100, description="0-100 score")
    trust_tier: str = Field(..., description="high, medium, or low")
    verification_status: str
    review_count: int = 0
    sentiment_summary: str
    red_flags: List[str] = []
    scraped_sources: List[str] = []
    
    # detailed breakdown
    details: Optional[Dict[str, Any]] = None
