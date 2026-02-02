# System Integration & Architecture Guide

## 1. Overview
The **Company Legitimacy Verification Pipeline (V2)** is a **Signal-Based System**. Instead of relying on a single binary "Verified" flag, it aggregates multiple trust signals from public web sources **and People Data Labs (PDL)** to calculate a `Trust Score`.

### Core Logic
*   **Enhanced PDL Search**: Prioritizes unique identifiers for high-accuracy enrichment:
    1.  **LinkedIn URL** (Highest Confidence)
    2.  **Website Domain**
    3.  **Company Name** (with auto-cleaning fallback)
*   **Dual Registry Search**: Verifies entity existence using both `Name + ID` (High Confidence) and `Name Only` (Broad) queries.
*   **Fuzzy Matching**: Uses Token-Set Ratio to handle name variations (e.g., "Google" vs "Google India Pvt Ltd").

---

## 2. Integration Points

### Input Schema (`CompanyInput`)
The Core Engine passes this object to `PipelineOrchestrator.run_pipeline()`:
```python
class CompanyInput(BaseModel):
    name: str              # e.g., "Zerodha Broking Ltd"
    country: str           # e.g., "India"
    registry_id: str       # e.g., "U65929KA2017PLC100661"
    
    # CRITICAL EXTENDED FIELDS
    linkedin_url: Optional[str] = None  # e.g., "https://www.linkedin.com/company/zerodha"
    website_urls: Optional[List[str]] = []
```

### Output Schema (`CredibilityAnalysis`)
The pipeline returns a rich analysis object.
```python
{
    "verification_status": "Verified",  # Verified | Pending
    "trust_score": 90.0,                # 0-100
    "trust_tier": "High",               # High | Medium | Low
    "details": {
        "pdl_data": { ... },            # Rich profile from People Data Labs
        "signals": {
            "registry_link_found": True,
            "registry_breakdown": {
                "zaubacorp.com": { "found": True, "verification_method": "strict_id" },
                "peopledatalabs.com": { "found": True }
            },
            "linkedin_verified": True
        }
    }
}
```

---

## 3. Universal Queuing Strategy

To support downstream tasks (like Sentiment Analysis or Manual Review), the pipeline now **Universal Queues** data.

*   **Mechanism**: All pipeline runs, regardless of `Verified` or `Pending` status, are pushed to the Redis queue.
*   **Queue Key**: `queue:sentiment_analysis`
*   **Payload**: Includes full `match_details`, `pdl_data`, and `score`.

---

## 4. Codebase Structure (Optimized)

| Component | Responsibility |
| :--- | :--- |
| `pipeline_orchestrator.py` | **Controller**. Manages flow, calculates scores, aggregates signals. |
| `lookup_engine.py` | **Router**. Handles Caching (Redis) and selects Providers. |
| `pdl_provider.py` | **Enrichment**. Interfaces with People Data Labs API (LinkedIn/Web/Name search). |
| `providers.py` | **Registry**. Implements Dual Search for Zauba/Tofler/Opencorporates. |
| `verify_cli.py` | **CLI**. "Hacker-style" tool for rapid testing and admin override. |

*(Legacy files and verbose comments have been aggressively cleaned.)*
