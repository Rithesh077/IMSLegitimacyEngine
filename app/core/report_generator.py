from fpdf import FPDF
from app.schemas.company import CredibilityAnalysis
import textwrap
import logging

logger = logging.getLogger(__name__)

class ReportGenerator(FPDF):
    def __init__(self, analysis: CredibilityAnalysis, company_name: str):
        super().__init__()
        self.analysis = analysis
        self.company_name = company_name
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

    def header(self):
        # Logo or Title
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Company Legitimacy Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def generate(self) -> str:
        """Generates the PDF and returns the filename."""
        self._add_title_section()
        self._add_score_section()
        self._add_summary_section()
        self._add_verification_details()
        self._add_red_flags()
        
        filename = f"reports/{self.company_name.replace(' ', '_')}_Report.pdf"
        import os
        os.makedirs("reports", exist_ok=True)
        self.output(filename)
        return filename

    def _add_title_section(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f"Target: {self.company_name}", 0, 1, 'L')
        self.ln(5)

    def _add_score_section(self):
        self.set_font('Arial', 'B', 12)
        score = self.analysis.trust_score
        
        # Color Coding
        if score >= 75:
            self.set_text_color(0, 150, 0)  # Green
        elif score >= 50:
            self.set_text_color(255, 165, 0) # Orange
        else:
            self.set_text_color(200, 0, 0)   # Red

        self.cell(0, 10, f"Trust Score: {score}/100 ({self.analysis.trust_tier})", 0, 1, 'L')
        self.set_text_color(0, 0, 0) # Reset
        self.ln(5)

    def _add_summary_section(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "Executive Summary", 0, 1, 'L')
        self.set_font('Arial', '', 11)
        
        # Determine strictness of wrapping based on page width
        summary_text = self.analysis.sentiment_summary
        
        # Basic sanitization
        summary_text = summary_text.replace("\u2019", "'").replace("\u2013", "-").replace("*", "")
        
        self.multi_cell(0, 7, summary_text)
        self.ln(5)

    def _add_verification_details(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "Verification Signals", 0, 1, 'L')
        self.set_font('Arial', '', 10)
        
        signals = self.analysis.details.get("signals", {})
        
        data = [
            ("Registry Found", signals.get("registry_link_found", False)),
            ("HR Contact Verified", signals.get("hr_verified", False)),
            ("Email Domain Match", signals.get("email_domain_match", False)),
            ("Address Verified", signals.get("address_verified", False)),
            ("LinkedIn Profile", signals.get("linkedin_verified", False)),
            ("Website Content", signals.get("website_content_match", False)),
        ]
        
        for label, val in data:
            status = "VERIFIED" if val else "NOT FOUND / UNVERIFIED"
            self.set_font('Arial', 'B', 10)
            self.cell(50, 8, label + ":", 0, 0)
            
            self.set_font('Arial', '', 10)
            if val:
                self.set_text_color(0, 128, 0)
            else:
                self.set_text_color(128, 0, 0)
            self.cell(0, 8, status, 0, 1)
            self.set_text_color(0, 0, 0)
            
        self.ln(5)

    def _add_red_flags(self):
        if not self.analysis.red_flags:
            return

        self.set_font('Arial', 'B', 12)
        self.set_text_color(200, 0, 0)
        self.cell(0, 10, "Red Flags / Concerns", 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 10)
        
        for flag in self.analysis.red_flags:
            # Clean flag text
            flag = flag.replace("\u2019", "'")
            # Use dash prefix to safely render bullet points
            self.multi_cell(0, 7, f"- {flag}")
