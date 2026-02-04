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
from app.engine.gemini_provider import GeminiProvider
from app.engine.pipeline_orchestrator import PipelineOrchestrator
from app.schemas.company import CompanyInput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_smart_parse_test():
    # 1. Simulate a Dummy Document (Text File)
    dummy_text = """
    OFFICIAL REGISTRATION DOCUMENT
    ------------------------------
    Company: TechNova Solutions Pvt Ltd
    Country: India
    Industry: Software Development
    Registration ID: U72900KA2020PTC123456
    Address: 123 Innovation Drive, Electronic City, Bangalore, India
    
    Contact:
    Mr. Rajesh Kumar (HR Director)
    Email: rajesh.k@technova.example.com
    Web: www.technova.example.com
    LinkedIn: linkedin.com/company/technova-solutions
    """
    
    # Ensure outputs directory exists
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, "dummy_doc.txt")
    
    with open(file_path, "w") as f:
        f.write(dummy_text)
        
    print("\n--- 1. Document Parsing ---")
    parsed = DocumentParser.parse(file_path)
    print(f"Extracted {len(parsed['content'])} chars.")
    
    print("\n--- 2. AI Extraction ---")
    ai = GeminiProvider()
    extracted_data = ai.extract_company_input(parsed['content'])
    print("Extracted Data:", extracted_data)
    
    if not extracted_data:
        print("Extraction failed. Aborting.")
        return

    print("\n--- 3. Legitimacy Pipeline ---")
    # Convert dict to Pydantic model
    try:
        input_obj = CompanyInput(**extracted_data)
        orchestrator = PipelineOrchestrator()
        result = await orchestrator.run_pipeline(input_obj)
        
        print("\n--- FINAL VERDICT ---")
        print(f"Company: {input_obj.name}")
        print(f"Trust Score: {result.trust_score}")
        print(f"Status: {result.verification_status}")
        print(f"Report: {result.details.get('report_path')}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_smart_parse_test())
