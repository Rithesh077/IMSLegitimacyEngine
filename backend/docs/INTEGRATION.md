# System Integration & Architecture Guide

## 1. Overview
The **Company Legitimacy Verification Pipeline (V2)** is a **Signal-Based System**. Instead of relying on a single binary "Verified" flag, it aggregates multiple trust signals from public web sources to calculate a `Trust Score`.

### Core Logic
*   **Dual Search Strategy**: Verifies entity existence using both `Name + ID` (High Confidence) and `Name Only` (Fallback) queries.
*   **Fuzzy Matching**: Uses Token-Set Ratio to handle name variations (e.g., "Google" vs "Google India Pvt Ltd").
*   **Granular Checks**: Returns specific `YES/NO` signals for each trusted domain (Zauba, Tofler, OpenCorporates, etc.).

---

## 2. Integration Points

### Input Schema (`CompanyInput`)
The Core Engine passes this object to `PipelineOrchestrator.run_pipeline()`:
```python
class CompanyInput(BaseModel):
    name: str              # e.g., "Zerodha Broking Ltd"
    country: str           # e.g., "India"
    registry_id: str       # e.g., "U65929KA2017PLC100661"
    
    # NEW OPTIONAL FIELDS
    linkedin_url: Optional[str] = None
    website_urls: Optional[List[str]] = []
```

### Output Schema (`CredibilityAnalysis`)
The pipeline returns a rich analysis object. **Do not destructively parse `details` keys unless specified.**
```python
{
    "verification_status": "Verified",  # Verified | Unverified
    "trust_score": 90.0,                # 0-100
    "trust_tier": "High",               # High | Medium | Low
    "details": {
        "signals": {
            "registry_link_found": True,
            "registry_breakdown": {
                "zaubacorp.com": True,
                "tofler.in": False,
                "mca.gov.in": True
            },
            "linkedin_verified": True,
            "website_content_match": True
        }
    }
}
```

---

## 3. Caching Strategy (Redis)

We utilize **Redis** to cache expensive search operations. This significantly reduces latency and API costs (or scraping risks) for repeated lookups.

### Implementation Reference
*   **Location**: `backend/app/engine/lookup_engine.py` -> `check_registry_presence`
*   **Key Format**: `registry:signal:{country}:{id}:{name}`
*   **TTL**: 86400 seconds (24 Hours)

```python
# Reference Code Snippet
async def check_registry_presence(...):
    # 1. READ THROUGH
    cached_data = await redis_client.get(cache_key)
    if cached_data: return json.loads(cached_data)

    # 2. FETCH & WRITE BACK
    breakdown = provider.check_registry_signal(...)
    await redis_client.set(cache_key, json.dumps(breakdown), ttl=86400)
    return breakdown
```

### Infrastructure Recommendation
*   **Development**: Use a local Redis instance (Docker or Native Windows Service).
    *   *Port*: 6379 (Default)
    *   *Env*: `REDIS_HOST=localhost`
*   **Production**: We strongly recommend a **Managed Redis Service** (e.g., **Aiven for Redis** or AWS ElastiCache).
    *   *Why?* Persistence, High Availability, and Auto-Scaling without maintenance overhead.
    *   *Setup*: Update `.env` with `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` provided by Aiven.

---

## 4. Codebase Structure (Cleaned for Handover)

| Component | Responsibility |
| :--- | :--- |
| `pipeline_orchestrator.py` | **Controller**. Manages flow, calculates scores, aggregates signals. |
| `lookup_engine.py` | **Router**. Handles Caching (Redis) and selects Country Providers. |
| `providers.py` | **Logic**. Implements the Dual Search Strategy for Registry verification. |
| `scraper.py` | **Utility**. Robust Web Search, Retries, and Fuzzy Matching logic. |
| `verify_cli.py` | **Testing**. CLI tool for rapid manual testing of the pipeline. |

*(Legacy files `registry_verifier.py`, `ml_verifier.py` have been removed.)*
