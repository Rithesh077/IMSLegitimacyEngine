import asyncio
import logging
import sys
import os
import warnings
from dotenv import load_dotenv

# Suppress deprecation warnings from google.generativeai
warnings.simplefilter('ignore', FutureWarning)

# Add parent directory to path so 'app' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables (API Keys)
load_dotenv()

from app.core.document_parser import DocumentParser
from app.engine.factory import get_ai_provider
from app.engine.pipeline_orchestrator import PipelineOrchestrator
from app.schemas.company import CompanyInput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_offer_test():
    # simulate dummy offer letter
    offer_text = """
    OFFER OF INTERNSHIP
    -------------------
    Date: 4th Feb 2026
    
    Dear Student,
    
    We are pleased to offer you the position of "Software Intern" at TechNova Solutions Pvt Ltd.
    Your monthly stipend will be INR 25,000.
    
    You will report to Mr. Rajesh Kumar.
    Please sign and return this via email to: hr_hiring@technova.example.com
    
    Sincerely,
    Mr. Rajesh Kumar (HR Manager)
    TechNova Solutions Pvt Ltd
    123 Innovation Drive, Bangalore, India
    """
    
    # ensure directories exist
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, 'inputs')
    report_dir = os.path.join(base_dir, 'reports')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    file_path = None
    
    # check for any valid file in inputs/ (prefer offer-like names if possible, else take first)
    valid_exts = [".pdf", ".docx", ".txt"]
    for f in os.listdir(input_dir):
        # simple heuristic to avoid picking up registration docs if both exist
        if "offer" in f.lower() or "intern" in f.lower():
             file_path = os.path.join(input_dir, f)
             break
    
    # fallback to any valid file if no specific offer file found
    if not file_path:
        for f in os.listdir(input_dir):
            if any(f.lower().endswith(ext) for ext in valid_exts):
                file_path = os.path.join(input_dir, f)
                break

    # if still no file, create dummy
    if not file_path:
        file_path = os.path.join(input_dir, "dummy_offer.txt")
        print(f"No input file found. Creating dummy: {file_path}")
        with open(file_path, "w") as f:
            f.write(offer_text)
    else:
        print(f"Found input file: {file_path}")
        
    print("\n--- 1. Parsing Offer Letter ---")
    parsed = DocumentParser.parse(file_path)
    
    print("\n--- 2. Validating Content ---")
    ai = get_ai_provider()
    offer_data = ai.extract_offer_details(parsed['content'])
    print("Extracted:", offer_data)
    
    if not offer_data or offer_data.get("error"):
        print(f"REJECTED: {offer_data.get('error', 'Empty response from AI')}")
        return
        
    print("VALID OFFER DETECTED")

    print("\n--- 3. Verifying Company Legitimacy ---")
    # map extracted offer data to companyinput
    input_obj = CompanyInput(
        name=offer_data.get("name", "Unknown"),
        country=offer_data.get("country", "India"), # default/inferred
        hr_name=offer_data.get("hr_name", "HR Team"), # default if not found
        hr_email=offer_data.get("hr_email"),
        industry="Unknown"
    )
    
    orchestrator = PipelineOrchestrator()
    result = await orchestrator.run_pipeline(input_obj)
    
    print("\n--- FINAL VERDICT ---")
    print(f"Trust Score: {result.trust_score}")
    print(f"Status: {result.verification_status}")
    print(f"Log: {result.details.get('report_path')}")

if __name__ == "__main__":
    asyncio.run(run_offer_test())
