# Legitimacy Engine API Integration Guide

Base URL: `https://imslegitimacyengine.onrender.com`
Authentication Header: `Legitimacy-engine-key: <your_api_key>`

This guide documents the core endpoints for the Company Legitimacy Pipeline.

## 1. Offer Letter Parsing (Step 1)

### Parse Offer Details
- **Endpoint**: `POST /verification/parse/offer-letter`
- **Description**: Extracts structured data from raw offer text (from OCR/PDF) and checks relevance to student's major.
- **Input (Form Data)**:
  ```json
  {
    "offer_text": "We are pleased to offer you the role of Data Engineer at TechCorp...",
    "student_programme": "BTech Computer Science"
  }
  ```
- **Output (JSON)**:
  ```json
  {
    "extracted_data": {
      "name": "TechCorp Solutions",
      "role": "Data Engineer",
      "stipend_mentioned": true,
      "is_offer_letter": true,
      "missing_fields": []
    },
    "relevance_analysis": {
      "is_relevant": true,
      "confidence_score": 95,
      "reasoning": "Data Engineer role aligns with CS curriculum."
    }
  }
  ```

---

## 2. Company Verification (Step 2)

### Verify Company Legitimacy
- **Endpoint**: `POST /verification/verify`
- **Response Time**: ~5-8 seconds

#### Verification Flow
| Phase | Checks | Timing |
|-------|--------|--------|
| **Mandatory (Fast)** | Registry lookup, Email domain check, AI analysis | Before response (~3-5s) |
| **Optional (Background)** | HR Name (Web Search), LinkedIn, Website, Address | After response |
| **DB Update** | Final score saved | **After** background checks complete |

> **Important:**
> The initial response relies on **Registry + Email Domain** only.
> **HR Name Verification** (`hr_verified`) will initially be `false` and updated later by the background process.

- **Input (JSON)**:
  ```json
  {
    "name": "Wipro Limited",
    "country": "India",
    "hr_name": "HR Team",
    "hr_email": "careers@wipro.com",
    "registry_id": "L32102KA1945PLC020800",
    "website_urls": ["https://www.wipro.com"]
  }
  ```
- **Output (JSON)**:
  ```json
  {
    "trust_score": 75.0,
    "trust_tier": "Verified",
    "verification_status": "Verified",
    "review_count": 0,
    "sentiment_summary": "Company found on registry, hr verified",
    "scraped_sources": [],
    "red_flags": [],
    "details": {
      "signals": {
        "registry_link_found": true,
        "email_domain_match": true,
        "hr_verified": true,
        "linkedin_verified": false,
        "website_verified": false
      },
      "registry_breakdown": { ... },
      "report_path": "reports/Wipro_Limited_Report.pdf",
      "note": "Initial score. Background checks in progress."
    }
  }
  ```

> **Note:** `trust_score` and `details` will be updated in the database after background checks (LinkedIn/Website) completion. Full PDF report available at `report_path`.

---

## 3. Faculty Allocation (Step 3)

### Recommend Guide
- **Endpoint**: `POST /verification/allocation/recommend`
- **Description**: Matches verified internship to the best available faculty based on expertise, interests, and workload.
- **Input (JSON)**:
  ```json
  {
    "student": {
      "id": "S001",
      "name": "Rahul Test",
      "internship_role": "ML Engineer",
      "internship_description": "Building computer vision models",
      "skills": ["Python", "TensorFlow"]
    },
    "available_faculty": [
      {
        "id": "F001",
        "name": "Dr. Ramesh",
        "department": "Computer Science",
        "expertise": ["Machine Learning", "AI"],
        "interests": ["Computer Vision"],
        "current_load": 2,
        "max_capacity": 8
      }
    ]
  }
  ```
- **Output (JSON)**:
  ```json
  {
    "recommended_faculty_id": "F001",
    "faculty_name": "Dr. Ramesh",
    "confidence_score": 92.5,
    "reasoning": "Strong match: Faculty expertise in ML aligns with role.",
    "alternatives": []
  }
  ```

---

## 4. Manual Override Check

### Validate Override Pair
- **Endpoint**: `POST /verification/allocation/validate-pair`
- **Description**: Checks if a manually assigned faculty is suitable for the student's internship.
- **Input (JSON)**:
  ```json
  {
    "student": {
      "internship_role": "Data Scientist",
      "internship_description": "Working on NLP models"
    },
    "faculty": {
      "expertise": ["Machine Learning", "NLP"]
    }
  }
  ```
- **Output (JSON)**:
  ```json
  {
    "is_suitable": true,
    "score": 90,
    "reasoning": "Faculty expertise in NLP directly matches internship domain."
  }
  ```

---

## 5. History

### View Verification History
- **Endpoint**: `GET /verification/history`
- **Description**: Returns log of all verification attempts.
- **Input**: None
- **Output (JSON)**:
  ```json
  {
    "count": 5,
    "history": [
      {
        "Company Name": "Infosys Limited",
        "Trust Score": 95,
        "Status": "Verified",
        "Timestamp": "2026-02-09 10:00:00"
      }
    ]
  }
  ```