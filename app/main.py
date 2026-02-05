from fastapi import FastAPI
from dotenv import load_dotenv
from app.verification.router import router as verification_router


# Load environment variables
load_dotenv()

app = FastAPI(title="Company Verification Service")

# Include routers
app.include_router(verification_router)



@app.get("/")
async def health_check():
    return {"status": "active", "service": "verification-engine"}
