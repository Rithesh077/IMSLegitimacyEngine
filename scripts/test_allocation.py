import asyncio
import logging
import sys
import os
import json
import warnings
from dotenv import load_dotenv

# Suppress deprecation warnings
warnings.simplefilter('ignore', FutureWarning)

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

from app.schemas.allocation import AllocationRequest
from app.engine.allocation_engine import AllocationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_allocation_test():
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, 'inputs')
    
    file_path = os.path.join(input_dir, "allocation_request.json")
    
    if not os.path.exists(file_path):
        print(f"Error: Input file not found at {file_path}")
        print("Please ensure 'inputs/allocation_request.json' exists.")
        return

    print(f"Reading request from: {file_path}")
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in input file.")
            return

    try:
        # Create Request Object
        request = AllocationRequest(**data)
        
        print("\n--- Running Allocation Engine ---")
        print(f"Student: {request.student.name}")
        print(f"Role: {request.student.internship_role}")
        print(f"Description: {request.student.internship_description}")
        print(f"Candidates: {len(request.available_faculty)}")
        
        # Run Engine
        engine = AllocationEngine()
        result = engine.allocate(request)
        
        print("\n--- ALLOCATION RESULT ---")
        print(f"Recommended Faculty: {result.faculty_name} (ID: {result.recommended_faculty_id})")
        print(f"Confidence Score: {result.confidence_score}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Random Fallback Used: {result.is_random_fallback}")
        
    except Exception as e:
        print(f"Allocation failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_allocation_test())
