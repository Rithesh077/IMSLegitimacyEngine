from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CompanyInput(BaseModel):
    """
    Basic input required to identify a company.
    """
    name: str = Field(..., description="Legal name of the company(e.g. 'Zomato Limited')")
    cin: Optional[str] = Field(None, description="Corporate Identification Number (India). 21 Characters.")
    domain: Optional[str] = Field(None, description="Official website domain (e.g. 'zomato.com')")

class VerificationResult(BaseModel):
    """
    Result of the official registry check.
    """
    is_registered: bool = False
    cin: Optional[str] = None
    registration_date: Optional[str] = None
    status: str = "Unknown"  # Active, Strike Off, Dissolved
    confidence_score: float = 0.0
    verification_source: str = "None"
    red_flags: List[str] = []
    
    # Metadata for next steps
    can_proceed_to_scraping: bool = False
