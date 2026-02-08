# Integration Guide: Company Legitimacy & Allocation Engine

This document is the **single source of truth** for integrating the Legitimacy Engine microservice into the main backend.

---

## 1. Architecture & Design Rationale
*(Why we built it this way)*

### The "Verification Engine" Pattern
We designed this service as a **standalone microservice** rather than a module within the main monolith.
*   **Reason**: Legitimacy verification involves heavy compute (AI analysis) and high-latency network calls (Web Scraping). Isolating it preventing blocking the main application's event loop.
*   **Database Strategy**: **Shared Database Pattern**. The engine writes directly to the `corporate_profiles` and `allocations` tables in the main Postgres DB. This avoids complex API-based data synchronization.

### Multi-Layered Verification
The pipeline uses a "Swiss Cheese Model" to catch illegitimate companies:
1.  **Registry Layer (MCA/CIN)**: Hard check against official government data.
2.  **Footprint Layer**: Checks if the website, LinkedIn, and email domain align.
3.  **AI Layer (Gemini)**: Reads between the lines (sentiment analysis, scam report aggregation).

---

## 2. Quick Start for Backend Team

### A. Authentication
Secure your requests with the shared secret key.
**Header**:
```http
Legitimacy-engine-key: <API_ACCESS_KEY>
```
*(Get this key from the `API_ACCESS_KEY` variable in the `.env` file)*

### B. Client Generation (No manual typing!)
We provide a standard **OpenAPI Specification**.
1.  Locate `docs/openapi.json` in this repo.
2.  Import it into **Postman** or **Swagger UI**.
3.  Or use a code generator to build a type-safe client for your backend (Node/Go/Python).

### C. Connect to Database
Ensure this service has the **same `DATABASE_URL`** as the main backend. It needs:
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
| **Verify Company** | `/verification/verify` | `POST` | Runs the full 3-layer check. Saves to DB. |
| **Allocate Guide** | `/verification/allocation/recommend` | `POST` | Matches student to faculty based on expertise. |
| **Parse Offer** | `/verification/parse/offer-letter` | `POST` | Extracts text from PDF to verify role relevance. |
| **Parse Registration** | `/verification/parse/recruiter-registration` | `POST` | Autofills company details from uploaded doc. |
| **Validate Pair** | `/verification/allocation/validate-pair` | `POST` | Checks if a manual student-faculty pair is valid. |
| **View History** | `/verification/history` | `GET` | Returns audit log of verifications. |

---

## 4. Troubleshooting

| Status Code | Meaning | Fix |
| :--- | :--- | :--- |
| **403 Forbidden** | Invalid/Missing Key | Check `Legitimacy-engine-key` header. |
| **422 Unprocessable** | Validation Error | Your JSON body is missing fields. Check `openapi.json`. |
| **500 Server Error** | Internal Crash | Check `reports/master_log.xlsx` or server logs. |

---