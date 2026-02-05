# Company Legitimacy Engine - Integration Manual

This manual provides the core development team with all necessary details to integrate the **Company Legitimacy Engine** into the main application.

## 1. API Endpoints Overview

The engine exposes the following RESTful endpoints via `app.verification.router`.

| Method | Endpoint | Description | Input | Output | Modules Used |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/verification/parse/recruiter-registration` | Parses Recruiter Registration Docs | `file` (UploadFile) | JSON (Company Details) | `DocumentParser`, `GeminiProvider` |
| **POST** | `/verification/parse/offer-letter` | Parses Student Offer Letters | `file` (UploadFile) | JSON (Offer Details) | `DocumentParser`, `GeminiProvider` |
| **POST** | `/verification/verify` | Runs Full Legitimacy Pipeline | JSON (`CompanyInput`) | JSON (`CredibilityAnalysis`) | `PipelineOrchestrator` |
| **GET** | `/verification/report/{filename}` | Download PDF Report | `filename` (str) | PDF File | `FileResponse` |
| **POST** | `/verification/allocation/recommend` | Recommend Faculty Guide | JSON (`AllocationRequest`) | JSON (`AllocationResponse`) | `AllocationEngine` |
| **GET** | `/verification/history` | Get All Verification Logs | None | JSON (List) | `ExcelLogger` (Reader) |

---

## 2. Endpoint Details

### A. Parse Recruiter Registration
**Purpose**: Auto-fill company details for recruiters during onboarding.
**URL**: `/verification/parse/recruiter-registration`
**Strict Enforcement**: Rejects files missing *Name, Country, HR Name, or HR Email*.

**Request (Multipart/Form-Data)**:
- `file`: The document to parse.

**Response (Success 200)**:
```json
{
  "name": "TechNova Solutions",
  "country": "India",
  "industry": "Software",
  "hr_name": "Rajesh Kumar",
  "hr_email": "rajesh@technova.com",
  "website_urls": ["www.technova.com"],
  "registered_address": "..."
}
```
**Response (Error 400)**:
```json
{ "detail": "Invalid Registration Document. Missing: country" }
```

### B. Parse Offer Letter
**Purpose**: Validate offer letters uploaded by students.
**URL**: `/verification/parse/offer-letter`
**Strict Enforcement**: Rejects files missing *Name, Country, HR Email, or Role*.

**Request**:
- `file`: Offer letter PDF/DOCX.

**Response (Success 200)**:
```json
{
  "name": "TechNova Solutions",
  "hr_email": "hr@technova.com",
  "role": "Software Intern",
  "stipend_mentioned": true,
  "is_offer_letter": true
}
```

### C. Verify Company
**Purpose**: The core engine. Runs Layer 1 (Registry) + Layer 2 (Footprint) + Layer 3 (AI) analysis.
**URL**: `/verification/verify`

**Request (JSON)**:
```json
{
  "name": "TechNova Solutions",
  "country": "India",
  "hr_name": "Rajesh Kumar",    // Optional but recommended
  "hr_email": "hr@technova.com", // Critical for domain check
  "website_urls": ["www.technova.com"]
}
```

**Response (JSON)**:
```json
{
  "trust_score": 85,
  "trust_tier": "High Trust",
  "verification_status": "VERIFIED",
  "sentiment_summary": "Company is registered with active status...",
  "details": {
      "report_path": "reports/TechNova_Report.pdf",
      "signals": { ... }
  }
}
```

### D. Download Report
**Purpose**: Retrieve the official PDF report generated during verification.
**URL**: `/verification/report/{filename}`
**Example**: `/verification/report/TechNova_Solutions_Report.pdf`
*(The filename is provided in the `/verify` response under `details.report_path`)*

### E. Recommend Faculty Guide
**Purpose**: Allocates a student to a faculty guide based on internship description matching.
**URL**: `/verification/allocation/recommend`
**Logic**: Semantic AI Match (Internship vs Expertise). Fallback to Random if no good match.

**Request**:
```json
{
  "student": {
    "id": "S123",
    "name": "Jane",
    "internship_role": "Blockchain Dev",
    "internship_description": "...",
    "skills": ["Solidity", "Rust"]
  },
  "available_faculty": [
    { "id": "F1", "name": "Prof X", "expertise": ["Crypto"] },
    { "id": "F2", "name": "Prof Y", "expertise": ["AI"] }
  ]
}
```

**Response**:
```json
{
  "recommended_faculty_id": "F1",
  "faculty_name": "Prof X",
  "confidence_score": 92.5,
  "reasoning": "Strong match on 'Crypto' vs 'Blockchain'.",
  "is_random_fallback": false
}
```

### F. Get History (Admin)
**Purpose**: Retrieve the full log of all verifications performed by the engine.
**URL**: `/verification/history`
**Response**:
```json
{
  "count": 5,
  "history": [
    {
      "Timestamp": "2026-02-04 14:30:00",
      "Company Name": "TechNova",
      "Trust Score": 85,
      "Status": "VERIFIED",
      ...
    }
  ]
}
```

---

## 3. Module Hierarchy (Internal Logic)

*   **`app.core.document_parser`**: Handles raw text extraction from `.pdf` and `.docx`.
*   **`app.engine.gemini_provider`**: The Brain.
    *   `extract_company_input()` / `extract_offer_details()`: Clean extraction logic using reliable fallback models.
    *   `analyze_company()`: The main fraud verification logic (uses Google Search Tool).
*   **`app.engine.lookup_engine`**: Connects to MCA (India) or OpenCorporates (Global) to check registration IDs.
*   **`app.engine.pipeline_orchestrator`**: Connects everything.
    *   Step 1: Check Registry.
    *   Step 2: Check Digital Footprint (Domain age, Website match).
    *   Step 3: AI Sentiment Analysis.
    *   Step 4: Generate Score & PDF Report.

## 4. Setup for the Team

1.  **Dependencies**:
    Ensure `requirements.txt` is installed. Key libs: `pypdf`, `python-docx`, `google-genai`.

2.  **Environment Variables (`.env`)**:
    ```ini
    GEMINI_API_KEY=AIz...
    # Optional
    # RAPIDAPI_KEY=... (If using paid registry lookup)
    # PDL_API_KEY=... (If using People Data Labs)
    ```

3.  **Output Directories**:
    *   `outputs/`: Intermediate extracted text (gitignored).
    *   `reports/`: Final PDF reports (gitignored).
    *   `logs/`: Excel Master Log (`master_log.xlsx`).

## 5. Testing
Run the verify scripts in `scripts/` to confirm the engine is working before integration.
*   `python scripts/test_smart_parse.py`
*   `python scripts/test_offer_letter.py`

## 6. Data Flow Architecture

This section defines exactly how data and media move through the system for each use case.

### A. Use Case: Recruiter Registration
1.  **Frontend**: Uploads PDF/DOCX to `/verification/parse/recruiter-registration`.
2.  **FastAPI**:
    *   Saves file to `outputs/temp_<filename>`.
    *   Passes path to `DocumentParser` -> Memory (Strings).
    *   Deletes `temp_<filename>` immediately after extracting text.
3.  **Engine**:
    *   Text -> `GeminiProvider` -> JSON.
4.  **Frontend**: Receives JSON (Company Name, HR Name, etc.) to auto-fill the form.

### B. Use Case: Student Offer Letter
1.  **Frontend**: Uploads Offer Letter PDF to `/verification/parse/offer-letter`.
2.  **FastAPI**:
    *   Saves file to `outputs/temp_<filename>`.
    *   Parses Text -> Deletes Temp File.
3.  **Engine**:
    *   Text -> `GeminiProvider` -> JSON (Strict Validation).
4.  **Frontend**: If Valid -> Calls `/verification/verify` with extracted data.

### C. Use Case: Company Verification
1.  **Input**: JSON Data (Name, Email, etc.) via `/verification/verify`.
2.  **Layer 1 (Registry)**:
    *   Engine calls Registry API (MCA/Zauba) -> Returns Registration Details.
3.  **Layer 2 (Footprint)**:
    *   Engine calls Google Search -> Returns Links & Snippets.
4.  **Layer 3 (AI Analysis)**:
    *   Aggregates L1 + L2 data -> Gemini API -> Trust Score & Analysis.
5.  **Output Generation**:
    *   **PDF**: Generated in `reports/<Company>_Report.pdf` (Persisted).
    *   **Excel**: Log appended to `reports/master_log.xlsx` (Persisted).
6.  **Response**: JSON containing Score + Path to PDF.

### D. Use Case: Recommendation System (Planned)
1.  **Input**: Resume (PDF) & Job Description (PDF/Text).
2.  **Processing**:
    *   File -> Text -> `Gemini Embedding API` -> Vector (List of Floats).
3.  **Storage**:
    *   Vectors stored in-memory (or Vector DB like FAISS/Chroma in future).
4.  **Matching**:
    *   Cosine Similarity(ResumeVector, JobVector) -> Score (0-1).
5.  **Output**: Ranked List of Candidates/Jobs.
