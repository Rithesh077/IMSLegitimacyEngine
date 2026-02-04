# Integration Guide: Company Legitimacy Microservice

This guide details how to integrate the Company Legitimacy Verification Microservice into your core application ecosystem.

## 1. Architecture Overview
This service operates as a standalone microservice exposing a REST API. It handles the complex logic of registry lookups, web scraping, and AI analysis, returning a consolidated trust signal.

*   **Protocol**: REST (JSON)
*   **Port**: 8001 (Default)
*   **Authentication**: None (Internal Service) / API Key (Optional Config)

## 2. API Endpoint

### Verify Company
**POST** `/verification/verify`

#### Request Schema
```json
{
  "name": "Zerodha Broking Limited",
  "industry": "Fintech",
  "country": "India",
  "registry_id": "U65990KA2010PTC054944",
  "website_urls": ["https://zerodha.com"],
  "linkedin_url": "https://linkedin.com/company/zerodha",
  "hr_name": "Nithin Kamath",
  "hr_email": "nithin@zerodha.com",
  "registered_address": "153/154, 4th Cross, J.P. Nagar 4th Phase, Bangalore"
}
```

*   `name` (Required): Official company name.
*   `country` (Optional): Default "India".
*   `registry_id` (Optional): CIN/LLPIN/GST for official lookup.
*   `hr_name` / `hr_email` (Optional): Used for association verification.

#### Response Schema
```json
{
  "trust_score": 85.0,
  "trust_tier": "High",
  "verification_status": "Verified",
  "sentiment_summary": "Company verified against official MCA registry. HR contact confirmed via public sources...",
  "details": {
    "report_path": "reports/Zerodha_Broking_Limited_Report.pdf",
    "signals": {
      "registry_link_found": true,
      "email_domain_match": true,
      "hr_verified": true
    }
  }
}
```

## 3. Integration Workflow

### Method A: Synchronous Blocking Call (Simple)
Call the API directly when you need an immediate answer (e.g., during Admin Review). Note: Latency is 5-20s due to AI/Scraping.

```python
import requests

def check_company(data):
    resp = requests.post("http://localhost:8001/verification/verify", json=data)
    if resp.status_code == 200:
        result = resp.json()
        if result['trust_score'] > 60:
            proceed_onboarding()
        else:
            flag_for_review(result['details']['report_path'])
```

### Method B: Asynchronous (Recommended)
For scale, trigger the verification in the background and use webhooks or polling (requires extending the service) or simply save the `report_path` for later consumption.

## 4. Artifacts Coverage
The service automatically generates:
1.  **PDF Report**: `reports/<Company>_Report.pdf` (User-facing proof).
2.  **Master Log**: `reports/master_log.xlsx` (Audit trail).

## 5. Environment Variables
Ensure these are set in the microservice's `.env`:
*   `GEMINI_API_KEY`: Required for AI Analysis.
*   `PDL_API_KEY`: Optional for enrichment.

## 6. Error Handling
*   **500 Internal Server Error**: Usually network or AI quota issues. The service attempts to return a partial result with `trust_score: 0` and error details in `analysis` if the AI fails mostly gracefully, but infrastructure crashes return 500.
