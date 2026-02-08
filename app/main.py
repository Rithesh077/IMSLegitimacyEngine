from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
import os
from app.verification.router import router as verification_router

# load environment variables
load_dotenv()

app = FastAPI(title="company verification service")

# security configuration
API_KEY_NAME = "Legitimacy-engine-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """validates the api key from the request header."""
    server_key = os.getenv("API_ACCESS_KEY", "").strip()
    if not api_key or api_key != server_key:
        raise HTTPException(status_code=403, detail="access denied: invalid api key")
    return api_key

# include routers with security dependency (globally applied or per-router)
# here we apply it to the verification router to protect all its endpoints
app.include_router(verification_router, dependencies=[Depends(verify_api_key)])

@app.get("/")
async def health_check():
    """public endpoint to check service health."""
    return {"status": "active", "service": "verification-engine"}
