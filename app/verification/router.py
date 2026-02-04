from fastapi import APIRouter, HTTPException
from app.schemas.company import CompanyInput, CredibilityAnalysis
from app.engine.pipeline_orchestrator import PipelineOrchestrator
import logging

router = APIRouter(prefix="/verification", tags=["Verification"])
logger = logging.getLogger(__name__)

@router.post("/verify", response_model=CredibilityAnalysis)
async def verify_company(data: CompanyInput):
    """
    Verifies a company's legitimacy using the multi-layered pipeline:
    1. Registry Lookup (if ID provided)
    2. Digital Footprint Analysis (LinkedIn/Website)
    3. HR & Address Association Verification
    4. AI Analysis (Gemini)
    """
    try:
        orchestrator = PipelineOrchestrator()
        result = await orchestrator.run_pipeline(data)
        return result
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File
import shutil
import os
from app.core.document_parser import DocumentParser
from app.engine.gemini_provider import GeminiProvider

@router.post("/parse/recruiter-registration")
async def parse_recruiter_registration(file: UploadFile = File(...)):
    """
    Uploads a Recruiter Registration Document (PDF/DOCX).
    Returns extracted structured data (Company Name, HR Info, etc.).
    Enforces mandatory fields: Name, Country, HR Name, HR Email.
    """
    temp_path = f"outputs/temp_{file.filename}"
    os.makedirs("outputs", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. Parse content
        raw = DocumentParser.parse(temp_path)
        
        # 2. Extract with AI (Strict Checks)
        ai = GeminiProvider()
        extracted_data = ai.extract_company_input(raw['content'])
        
        # 3. Handle Errors
        if extracted_data.get("error"):
             raise HTTPException(status_code=400, detail=extracted_data["error"])
             
        return extracted_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/parse/offer-letter")
async def parse_offer_letter(file: UploadFile = File(...)):
    """
    Uploads a Student Offer Letter (PDF/DOCX).
    Returns extracted details.
    Enforces mandatory fields: Name, Country, HR Email, Role.
    """
    temp_path = f"outputs/temp_{file.filename}"
    os.makedirs("outputs", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. Parse content
        raw = DocumentParser.parse(temp_path)
        
        # 2. Extract with AI (Strict Checks)
        ai = GeminiProvider()
        extracted_data = ai.extract_offer_details(raw['content'])
        
        # 3. Handle Errors
        if extracted_data.get("error"):
             raise HTTPException(status_code=400, detail=extracted_data["error"])
             
        return extracted_data
        
    except HTTPException as he:
        raise he
from fastapi.responses import FileResponse
from openpyxl import load_workbook

@router.get("/report/{filename}")
async def get_report(filename: str):
    """
    Downloads a specific PDF report.
    Example: 'TechNova_Solutions_Report.pdf'
    """
    file_path = f"reports/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

@router.get("/history")
async def get_verification_history():
    """
    Returns the full verification history from the Master Excel Log.
    Useful for Admin Dashboards.
    """
    log_path = "reports/master_log.xlsx"
    if not os.path.exists(log_path):
        return {"history": []}
        
    try:
        wb = load_workbook(log_path, read_only=True)
        ws = wb.active
        
        data = []
        headers = [cell.value for cell in ws[1]]
        
        for row in ws.iter_rows(min_row=2, values_only=True):
            entry = dict(zip(headers, row))
            data.append(entry)
            
        return {"count": len(data), "history": data}
    except Exception as e:
        logger.error(f"Failed to read history: {e}")
        raise HTTPException(status_code=500, detail="Could not read history log")
