from fastapi import FastAPI
from dotenv import load_dotenv
from app.verification.router import router as verification_router
from app.core.redis import redis_client

# Load environment variables
load_dotenv()

app = FastAPI(title="Company Verification Service")

# Include routers
app.include_router(verification_router)

@app.on_event("startup")
async def startup():
    """Connect to Redis on startup"""
    pass

@app.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown"""
    pass

@app.get("/")
async def health_check():
    return {"status": "active", "service": "verification-engine"}
