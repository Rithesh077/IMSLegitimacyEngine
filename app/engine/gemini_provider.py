import os
import json
import time
import hashlib
import logging
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from app.core.cache import cache_get, cache_set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiProvider:
    """handles all gemini ai calls with retry, caching, and key rotation."""
    
    def __init__(self):
        self.api_keys = []
        
        k1 = os.getenv("GEMINI_API_KEY")
        if k1: self.api_keys.append(k1)
        
        i = 2
        while True:
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if not k: break
            self.api_keys.append(k)
            i += 1
            
        if not self.api_keys:
            logger.warning("no gemini api keys found. ai features disabled.")
            self.current_key_index = 0
        else:
            logger.info(f"loaded {len(self.api_keys)} gemini api keys.")
            self.current_key_index = 0
            self._configure_client()

        # available models - ordered by speed/capability
        self.models = [
            "gemini-2.5-flash",           # primary - fastest 2.5
            "gemini-2.0-flash",           # fallback - reliable
            "gemini-2.0-flash-lite",      # lightweight fallback
            "gemini-2.5-flash-preview-05-20",  # preview version
            "gemini-2.5-pro-preview-05-06",    # pro preview
        ]

    def _configure_client(self):
        """configures genai with current api key."""
        if self.api_keys:
            key = self.api_keys[self.current_key_index]
            genai.configure(api_key=key)

    def _rotate_key(self):
        """rotates to next api key on quota errors."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._configure_client()
            logger.info(f"rotated to api key #{self.current_key_index + 1}")

    def _get_cache_key(self, prompt: str) -> str:
        """generates cache key from prompt hash."""
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()

    def _generate_with_fallback(self, prompt: str, cache_ttl: int = 86400) -> Dict[str, Any]:
        """fast generation with proper model fallback and redis cache."""
        cache_key = f"gemini:{self._get_cache_key(prompt)}"
        
        cached = cache_get(cache_key)
        if cached:
            return cached

        errors = []
        
        for model_name in self.models:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(
                    prompt,
                    request_options={"timeout": 15}
                )
                
                result = self._parse_json(resp.text)
                if result and not result.get("error"):
                    cache_set(cache_key, result, cache_ttl)
                    logger.info(f"success with {model_name}")
                    return result
                    
            except Exception as e:
                err_str = str(e)
                errors.append(f"{model_name}: {err_str[:50]}")
                
                if "429" in err_str or "quota" in err_str.lower():
                    self._rotate_key()
                    logger.warning(f"{model_name} quota hit, trying next model...")
                    continue  # immediately try next model
                elif "500" in err_str or "503" in err_str:
                    time.sleep(0.2)
                    continue
                else:
                    continue  # try next model on any error
        
        logger.error(f"all {len(errors)} models failed")
        return {"error": "all models failed", "details": errors}

    def analyze_company(self, company_name: str, layer1_data: Dict[str, Any], reputation_data: list) -> Dict[str, Any]:
        """ai analysis of company legitimacy."""
        if not self.api_keys:
            return {"trust_score": 50, "analysis": "skipped (no key)", "flags": []}

        prompt = self._build_company_prompt(company_name, layer1_data, reputation_data)
        result = self._generate_with_fallback(prompt)
        
        if result.get("error"):
            return {
                "trust_score": 0, 
                "classification": "Unknown", 
                "analysis": f"ai failed: {result.get('error')}",
                "flags": ["AI_ERROR"]
            }
        return result

    def extract_company_input(self, raw_text: str) -> Dict[str, Any]:
        """extracts company registration details from document."""
        if not self.api_keys:
            return {}

        prompt = f"""
extract company registration details from the text below into json.

text:
{raw_text[:4000]}

output json:
{{
    "name": "legal company name",
    "industry": "industry sector",
    "country": "country of registration",
    "registry_id": "cin/ein or null",
    "website_urls": ["urls"],
    "linkedin_url": "url or null",
    "hr_name": "contact person name",
    "hr_email": "contact email",
    "registered_address": "address or null"
}}
"""
        
        data = self._generate_with_fallback(prompt)
        if data.get("error"):
            return {"error": data["error"]}

        if "website_urls" in data and isinstance(data["website_urls"], str):
            data["website_urls"] = [data["website_urls"]]
        
        required = ["name", "country", "hr_name", "hr_email"]
        missing = [f for f in required if not data.get(f)]
            
        if missing:
            data["error"] = f"missing required fields: {', '.join(missing)}"
        
        return data

    def extract_offer_details(self, raw_text: str) -> Dict[str, Any]:
        """extracts offer letter details."""
        if not self.api_keys:
            return {}

        prompt = f"""
analyze this job/internship offer letter and extract details.

text:
{raw_text[:4000]}

output json:
{{
    "name": "company legal name",
    "country": "country",
    "hr_name": "signatory/hr name",
    "hr_email": "sender email",
    "role": "job title offered",
    "stipend_mentioned": true/false,
    "is_offer_letter": true/false,
    "missing_fields": ["list of missing critical fields"]
}}
"""
        
        data = self._generate_with_fallback(prompt)
        if data.get("error"):
            return {"error": data["error"]}

        required = ["name", "country", "hr_name", "hr_email", "role"]
        missing = [f for f in required if not data.get(f)]
        
        if missing or not data.get("is_offer_letter"):
            data["error"] = f"invalid offer letter. missing: {', '.join(missing)}"
        
        return data

    def verify_internship_relevance(self, raw_text: str, student_context: str) -> Dict[str, Any]:
        """checks if internship is relevant to student's academic programme."""
        if not self.api_keys:
            return {"is_relevant": False, "error": "no api key"}

        prompt = f"""
you are an academic internship coordinator. determine if this internship offer is relevant for the student.

STUDENT PROGRAMME: {student_context}

OFFER LETTER TEXT:
{raw_text[:3500]}

TASK:
1. identify the job role and key responsibilities from the offer letter.
2. extract the core subjects from the student's programme name:
   - "bsc computer science, statistics and mathematics" → computer science, statistics, mathematics
   - "btech mechanical engineering" → mechanical engineering
   - "msc data science" → data science, statistics, machine learning

3. determine relevance by checking if the role aligns with career paths for those subjects:
   - software/web dev, data analyst, ml engineer → relevant for cs, statistics, math
   - finance analyst, actuarial → relevant for statistics, math, economics
   - mechanical design, cad → relevant for mechanical engineering
   
4. flag as NOT relevant if:
   - role is "campus ambassador", "social media marketing", "data entry" for technical programmes
   - role is mlm/pyramid scheme type
   - role has zero connection to any subject in the programme

output json:
{{
    "is_relevant": true/false,
    "confidence_score": 0-100,
    "detected_role": "extracted job title",
    "detected_subjects": ["subjects extracted from programme"],
    "reasoning": "one line explanation"
}}
"""
        
        return self._generate_with_fallback(prompt)

    def match_guide(self, student_json: Dict[str, Any], faculty_list: list) -> Dict[str, Any]:
        """matches student to best faculty guides based on expertise and interests."""
        if not self.api_keys:
            return {}

        prompt = f"""
match this student to the best faculty guides based on alignment with faculty expertise and research interests.

STUDENT INTERNSHIP:
role: {student_json.get('internship_role')}
description: {student_json.get('internship_description')}
skills: {student_json.get('skills')}

FACULTY LIST (includes expertise and interests):
{json.dumps(faculty_list, indent=2)}

MATCHING CRITERIA:
1. expertise match: faculty's area of expertise aligns with student's internship role/skills
2. interest match: faculty's research interests overlap with student's work description
3. prioritize faculty with BOTH matching expertise AND relevant interests

select top 3 matches with expertise scores (0-100).

output json:
{{
    "ranked_matches": [
        {{
            "faculty_id": "id",
            "faculty_name": "name",
            "expertise_score": 0-100,
            "reasoning": "brief reason mentioning expertise/interest match"
        }}
    ]
}}
"""

        return self._generate_with_fallback(prompt)

    def _build_company_prompt(self, name: str, l1: Dict[str, Any], rep: list) -> str:
        """builds prompt for company analysis."""
        signals = l1.get('signals', {})
        hr = l1.get('hr_data', {})
        addr = l1.get('address_data', {})
        
        return f"""
analyze company '{name}' for legitimacy.

provided data:
- industry: {l1.get('industry') or 'unknown'}
- registry found: {signals.get('registry_link_found')}
- hr verified: {signals.get('hr_verified')} (name: {hr.get('name')})
- address verified: {signals.get('address_verified')}
- linkedin verified: {signals.get('linkedin_verified')}
- website match: {signals.get('website_content_match')}
- reputation signals: {json.dumps(rep[:5])}

task:
1. calculate trust score (0-100)
2. classify: "high trust", "review needed", or "low trust"
3. list any red flags found

output json:
{{
    "trust_score": 0-100,
    "classification": "category",
    "analysis": "brief summary",
    "flags": ["list of concerns if any"]
}}
"""

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """parses json from llm response."""
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start != -1 and end > start:
                clean = clean[start:end]
            return json.loads(clean)
        except Exception as e:
            return {"error": f"json parse failed: {str(e)[:50]}"}
