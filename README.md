# Company Legitimacy & Allocation Service

A multi-modal microservice for verifying company legitimacy and allocating faculty guides to students. This system combines official registry lookups (MCA/CIN), AI-driven sentiment analysis (Gemini), and digital footprint verification.

## Features

*   **Multi-Layer Verification**:
    *   **Layer 1**: Official Registry Lookup (India MCA, etc.).
    *   **Layer 2**: Digital Footprint (LinkedIn, Website, Email Domain).
    *   **Layer 3**: AI Sentiment Analysis & Scam Detection.
*   **Document Parsing**: Extract data from Recruiter Registrations and Offer Letters (PDF/Docx).
*   **Faculty Allocation**: Intelligent matching of students to faculty guides based on domain expertise and workload.
*   **Database Integrated**: Persists all profiles and allocations to PostgreSQL.
*   **Excel Logging**: Maintains a backup log in `reports/master_log.xlsx`.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file:
    ```ini
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
    GEMINI_API_KEY=your_key_here
    API_ACCESS_KEY=your_secure_secret (Generate using scripts/generate_key.py)
    ```

3.  **Initialize Database**:
    Run this script once to create tables (`corporate_profiles`, `allocations`, `User`):
    ```bash
    python scripts/init_db.py
    ```

## Running the Service

### Start Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```
*(Port 8001 is default to avoid conflict with other services)*

### Verify Deployment
We have a self-contained test script to verify the API and Database connection before going live:
```bash
python scripts/test_deployment.py
```

## API Documentation

**See [docs/INTEGRATION.md](docs/INTEGRATION.md) for the complete API Reference.**

### Quick Endpoint Summary
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/verification/verify` | Full company legitimacy check |
| `POST` | `/verification/parse/offer-letter` | Extract details from offer letters |
| `POST` | `/verification/allocation/recommend` | Get faculty guide recommendation |
| `GET` | `/verification/history` | View verification logs |

## Project Structure
*   `app/engine`: Core logic (Orchestrator, Scraper, Sentiment).
*   `app/models`: Database schemas (SQLAlchemy).
*   `app/verification`: API Routes.
*   `docs/`: Integration guides and API specs.
*   `scripts/`: Utilities for DB init, key generation, and testing.
