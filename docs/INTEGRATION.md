# Integration Guide: Company Legitimacy & Allocation Engine

This document is the **single source of truth** for integrating the Legitimacy Engine microservice into the main backend.

---

## 1. Architecture & Design Rationale

### The "Verification Engine" Pattern
We designed this service as a **standalone microservice** rather than a module within the main monolith.
*   **Reason**: Legitimacy verification involves heavy compute (AI analysis) and high-latency network calls (Web Scraping). Isolating it prevents blocking the main application's event loop.
*   **Database Strategy**: **Shared Database Pattern**. The engine writes directly to the `corporate_profiles` and `allocations` tables in the main Postgres DB.

### Multi-Layered Verification
The pipeline uses a "Swiss Cheese Model" to catch illegitimate companies:
1.  **Registry Layer (MCA/CIN)**: Hard check against official government data.
2.  **Footprint Layer**: Checks if the website, LinkedIn, and email domain align.
3.  **AI Layer (Gemini)**: Reads between the lines (sentiment analysis, scam report aggregation).

### Caching Strategy
*   **Primary**: Redis (Render Key Value / Upstash)
*   **Fallback**: In-memory cache (when Redis unavailable)
*   **TTL**: 24 hours for AI responses
*   **Result**: ~59x faster for cached requests

---

## 2. Quick Start for Backend Team

### A. Environment Variables
```env
GEMINI_API_KEY=your_gemini_key
API_ACCESS_KEY=your_shared_secret
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://red-xxxxx:6379  # Optional but recommended
```

### B. Authentication
Secure your requests with the shared secret key.
```http
Legitimacy-engine-key: <API_ACCESS_KEY>
```

### C. Client Generation
We provide a standard **OpenAPI Specification**.
1.  Locate `docs/openapi.json` in this repo.
2.  Import it into **Postman** or **Swagger UI**.
3.  Or use a code generator to build a type-safe client.

### D. Database Access
Ensure this service has the **same `DATABASE_URL`** as the main backend:
*   `READ/WRITE` on `corporate_profiles`
*   `READ/WRITE` on `allocations`
*   `READ` on `User` (for fetching student/faculty profiles)

---

## 3. API Reference

### Base URL
`https://<your-deploy-url>` (e.g., `http://localhost:8001`)

### Endpoints Summary

| Feature | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Health Check** | `/` | `GET` | Returns service status. |
| **Verify Company** | `/verification/verify` | `POST` | Runs the full 3-layer check. Saves to DB. |
| **Parse Offer Letter** | `/verification/parse/offer-letter` | `POST` | Extracts company info & checks role relevance. |
| **Parse Registration** | `/verification/parse/recruiter-registration` | `POST` | Autofills company details from uploaded doc. |
| **Allocate Guide** | `/verification/allocation/recommend` | `POST` | Matches student to faculty based on expertise. |
| **Validate Pair** | `/verification/allocation/validate-pair` | `POST` | Checks if a manual student-faculty pair is valid. |
| **View History** | `/verification/history` | `GET` | Returns audit log of verifications. |

---

## 4. Deployment (Render)

### Web Service
*   **Build**: `pip install -r requirements.txt`
*   **Start**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Redis Cache (Key Value)
1. Create a **Key Value** instance (free tier: 25MB)
2. Copy the **Internal URL**
3. Add to Web Service environment: `REDIS_URL=<Internal URL>`

---

## 5. AI Models

The engine uses multiple Gemini models with automatic fallback:

| Priority | Model | Speed |
| :--- | :--- | :--- |
| 1 | gemini-2.5-flash | Fastest |
| 2 | gemini-2.5-pro | Fast |
| 3 | gemini-2.0-flash | Fast |
| 4 | gemini-1.5-flash-002 | Stable |
| 5 | gemini-1.5-flash | Stable |
| 6 | gemini-1.5-flash-8b | Lightweight |
| 7 | gemini-1.5-pro-002 | Capable |
| 8 | gemini-1.5-pro | Stable |
| 9 | gemini-pro | Legacy |

---

## 6. Troubleshooting

| Status Code | Meaning | Fix |
| :--- | :--- | :--- |
| **403 Forbidden** | Invalid/Missing Key | Check `Legitimacy-engine-key` header. |
| **422 Unprocessable** | Validation Error | Your JSON body is missing fields. Check `openapi.json`. |
| **429 Too Many Requests** | Gemini quota exceeded | Add more API keys or wait. |
| **500 Server Error** | Internal Crash | Check server logs. |

---

## 7. Testing

Run the workflow test script locally:
```powershell
.\scripts\workflow_test.ps1
```

Run the speed test to verify caching:
```powershell
.\scripts\speed_test.ps1
```

---