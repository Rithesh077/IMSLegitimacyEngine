from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.company import CompanyInput, CredibilityAnalysis
from app.schemas.allocation import AllocationRequest, AllocationResponse
from app.engine.pipeline_orchestrator import PipelineOrchestrator
from app.engine.factory import get_ai_provider
from app.engine.allocation_engine import AllocationEngine
from app.core.document_parser import DocumentParser
from app.core.database import get_db
from openpyxl import load_workbook
import logging
import shutil
import os

router = APIRouter(prefix="/verification", tags=["Verification"])
logger = logging.getLogger(__name__)

@router.post("/verify", response_model=CredibilityAnalysis)
async def verify_company(data: CompanyInput, db: AsyncSession = Depends(get_db)):
    """
    verifies company legitimacy using:
    1. registry lookup
    2. digital footprint analysis
    3. hr & address verification
    4. ai analysis
    """
    try:
        orchestrator = PipelineOrchestrator()
        result = await orchestrator.run_pipeline(data, db)
        return result
    except Exception as e:
        logger.error(f"verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse/recruiter-registration")
async def parse_recruiter_registration(file: UploadFile = File(...)):
    """
    parses recruiter registration doc (pdf/docx).
    returns structured data (name, country, hr info).
    """
    temp_path = f"outputs/temp_{file.filename}"
    os.makedirs("outputs", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # parse content
        raw = DocumentParser.parse(temp_path)
        
        # extract with ai
        ai = get_ai_provider()
        extracted_data = ai.extract_company_input(raw['content'])
        
        # handle errors
        if extracted_data.get("error"):
             raise HTTPException(status_code=400, detail=extracted_data["error"])
             
        return extracted_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/parse/offer-letter")
async def parse_offer_letter(file: UploadFile = File(...), student_major: str = Form(...)):
    """
    parses offer letter and checks relevance to major.
    """
    temp_path = f"outputs/temp_{file.filename}"
    os.makedirs("outputs", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # parse content
        raw = DocumentParser.parse(temp_path)
        
        ai = get_ai_provider()
        
        # 1. extract details
        extracted_data = ai.extract_offer_details(raw['content'])

        # 2. check relevance
        relevance = ai.verify_internship_relevance(raw['content'], student_major)
        
        # handle errors (lax constraint)
        if extracted_data.get("error"):
             pass 
        
        return {
            "extracted_data": extracted_data,
            "relevance_analysis": relevance
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/report/{filename}")
async def get_report(filename: str):
    """
    downloads specific pdf report.
    """
    file_path = f"reports/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    return {"error": "file not found"}

@router.post("/allocation/recommend", response_model=AllocationResponse)
async def recommend_guide(request: AllocationRequest):
    """
    recommends faculty guides based on requirements.
    """
    engine = AllocationEngine()
    result = engine.allocate(request)
    return result

@router.post("/allocation/validate-pair")
async def validate_allocation_pair(request: dict):
    """
    validates manual student-faculty pair.
    """
    engine = AllocationEngine()
    student = request.get("student")
    faculty = request.get("faculty")
    
    if not student or not faculty:
        raise HTTPException(status_code=400, detail="missing data")
        
    return engine.validate_pair(student, faculty)

@router.get("/history")
async def get_verification_history():
    """
    returns the full verification history from the master excel log.
    useful for admin dashboards.
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
        logger.error(f"failed to read history: {e}")
        raise HTTPException(status_code=500, detail="could not read history log")
