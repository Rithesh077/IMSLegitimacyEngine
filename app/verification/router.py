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
