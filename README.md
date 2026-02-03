# Company Legitimacy Verification Service

A standalone microservice for assessing company legitimacy using a multi-layered verification pipeline.

## Features
*   **Dual-Layer Verification**: Combines Registry Lookups (Layer 1) with AI Analysis (Layer 2).
*   **Trust Score**: Generates a 0-100 confidence score and trust classification (High/Review/Low).
*   **Microservice Architecture**: Decoupled FastAPI application ready for integration.
*   **Real-time Analysis**: Live verification without queuing dependencies.

## Setup

1.  **Navigate to the service directory:**
    ```bash
    cd verification_engine
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration:**
    Create a `.env` file in the root of `verification_engine`:
    ```ini
    GEMINI_API_KEY=your_google_api_key_here
    PDL_API_KEY=your_pdl_key_here (Optional)
    REDIS_HOST=localhost (Optional, currently disabled)
    ```

## Running the Service

Start the server using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The API will be available at: `http://localhost:8001`

## API Reference

### Verify Company
**Endpoint:** `POST /verification/verify`

**Request Body:**
```json
{
  "name": "Company Name",
  "country": "Country Code (e.g., India, USA)",
  "hr_name": "HR/Recruiter Name",
  "hr_email": "recruiter@company.com",
  "industry": "Technology",
  "website_urls": ["https://company.com"],
  "linkedin_url": "https://linkedin.com/company/example",
  "registry_id": "Optional Registry ID (CIN/EIN)",
  "registered_address": "Optional Physical Address"
}
```

**Response:**
```json
{
  "trust_score": 95.0,
  "trust_tier": "High",
  "verification_status": "Verified",
  "sentiment_summary": "Legitimate entity. Verified via ...",
  "red_flags": [],
  "details": {
      "signals": { ... }
  }
}
```

## Integration Example (Python)

```python
import httpx
import asyncio

async def verify_remote():
    url = "http://localhost:8001/verification/verify"
    payload = {
        "name": "Zerodha",
        "country": "India",
        "hr_name": "Venu Madhav",
        "hr_email": "venu@zerodha.com"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(response.json())

if __name__ == "__main__":
    asyncio.run(verify_remote())
```
