import re
from typing import Optional
from app.schemas.company import CompanyInput, VerificationResult

class RegistryVerifier:
    """
    Verifies company details against official patterns (like CIN).
    Acts as the 'Gatekeeper' before we spend resources on web scraping.
    """
    def __init__(self):
        # Regex for verifying Indian CIN (Corporate Identity Number) format
        # Pattern Breakdown:
        # [LU]      : Listed or Unlisted (1 char)
        # [0-9]{5}  : Industry Code (5 digits)
        # [A-Z]{2}  : State Code (2 chars, e.g., MH, KA)
        # [0-9]{4}  : Year of Incorporation (4 digits)
        # [A-Z]{3}  : Ownership Type (3 chars, e.g., PLC, PTC)
        # [0-9]{6}  : Registration Number (6 digits)
        self.cin_pattern = re.compile(r'^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$')

    def verify_company(self, input_data: CompanyInput) -> VerificationResult:
        """
        main entry point for verification.
        checks if the input data (cin) is valid.
        """
        result = VerificationResult(
            is_registered=False,
            cin=input_data.cin,
            status="Unknown",
            can_proceed_to_scraping=False
        )

        # direct cin verification
        if input_data.cin:
            if self._validate_cin_format(input_data.cin):
                result.cin = input_data.cin
                result.is_registered = True
                result.status = "Format Validated"
                result.confidence_score = 80.0  # high confidence if cin format matches
                result.verification_source = "CIN Pattern Match"
                
                # if registered, we definitely want to scrape for reputation/scams
                result.can_proceed_to_scraping = True 
            else:
                result.red_flags.append("Invalid CIN Information Provided")
                result.confidence_score = 0.0
                result.status = "Invalid CIN"
                # even if cin is bad, we might want to see if the name brings up scam reports
                result.can_proceed_to_scraping = True
                
        # no cin provided (name only)
        else:
            if input_data.name:
                result.status = "Unregistered / No ID"
                result.confidence_score = 10.0 # low confidence without id
                result.verification_source = "None"
                result.red_flags.append("No CIN provided")
                
                # must scrape to find any info at all
                result.can_proceed_to_scraping = True
            else:
                result.status = "Invalid Input"
                result.red_flags.append("No Name or CIN provided")
                result.can_proceed_to_scraping = False
        
        return result

    def _validate_cin_format(self, cin: str) -> bool:
        """Checks if the CIN string matches the standard Indian format."""
        if not cin:
            return False
        return bool(self.cin_pattern.match(cin.upper()))
