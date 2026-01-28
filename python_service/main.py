from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import scrape_company_data
from analyzer import analyze_credibility

app = FastAPI()

class CompanyRequest(BaseModel):
    name: str
    govt_id: str | None = None
    website: str | None = None

@app.post("/analyze")
async def analyze_company(request: CompanyRequest):
    try:
        # 1. Scrape Data
        scraped_data = await scrape_company_data(request.name, request.govt_id)
        
        # 2. Analyze Sentiment & Legitimacy
        result = analyze_credibility(scraped_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
