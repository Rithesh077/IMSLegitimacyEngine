import re
from .models import CompanyInput, VerificationResult

class RegistryVerifier:
    def __init__(self):
        # Regex for verifying Indian CIN format
        # L/U (Listed/Unlisted) + 5 digits (Industry) + 2 letters (State) + 4 digits (Year) + 3 letters (Ownership) + 6 digits (Reg #)
        self.cin_pattern = re.compile(r'^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$')

    def verify_company(self, input_data: CompanyInput) -> VerificationResult:
        result = VerificationResult(
            is_registered=False,
            cin=input_data.cin,
            status="Unknown",
            can_proceed_to_scraping=False
        )

        # 1. Direct CIN Verification
        if input_data.cin:
            if self._validate_cin_format(input_data.cin):
                result.cin = input_data.cin
                result.is_registered = True
                result.status = "Format Validated"
                result.confidence_score = 100.0
                result.verification_source = "Deep Formatting Check"
                result.can_proceed_to_scraping = True
            else:
                result.red_flags.append("Invalid CIN Format Provided")
                result.confidence_score = 0.0
                return result

        # 2. TODO: If no CIN, we would implement the Name -> CIN lookup here.
        # For now, if no CIN is provided, we flag it.
        if not input_data.cin and input_data.name:
            result.red_flags.append("No CIN provided. Automatic Name Lookup not yet connected.")
            result.confidence_score = 10.0 # Low confidence just on name
        
        return result

    def _validate_cin_format(self, cin: str) -> bool:
        """Checks if the CIN string matches the standard Indian format."""
        if not cin:
            return False
        return bool(self.cin_pattern.match(cin.upper()))
