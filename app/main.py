from fastapi import FastAPI
from dotenv import load_dotenv
from app.verification.router import router as verification_router
from app.core.redis import redis_client

# Load environment variables
load_dotenv()

app = FastAPI(title="Company Verification Service")

# Include the verification router
app.include_router(verification_router)

@app.on_event("startup")
async def startup():
    """Connect to Redis on startup"""
    # try:
    #     await redis_client.connect()
    # except Exception as e:
    #     print(f"Warning: Redis connection failed on startup: {e}")
    pass

@app.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown"""
    # await redis_client.close()
    pass

@app.get("/")
async def health_check():
    return {"status": "active", "service": "verification-engine"}
