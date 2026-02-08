from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
import os
from app.verification.router import router as verification_router

load_dotenv()

app = FastAPI(title="company verification service")

API_KEY_NAME = "Legitimacy-engine-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """validates api key from request header."""
    server_key = os.getenv("API_ACCESS_KEY", "").strip()
    if not api_key or api_key != server_key:
        raise HTTPException(status_code=403, detail="access denied: invalid api key")
    return api_key

app.include_router(verification_router, dependencies=[Depends(verify_api_key)])

@app.get("/")
async def health_check():
    """public health check endpoint."""
    return {"status": "active", "service": "verification-engine"}
