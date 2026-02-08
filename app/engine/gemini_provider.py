import os
import logging
import json
import google.generativeai as genai
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GeminiProvider:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("gemini api key missing")
        else:
            genai.configure(api_key=self.api_key)
        
        self.models = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-flash-latest",
            "gemini-pro-latest",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]

    def analyze_company(self, company_name: str, layer1_data: Dict[str, Any], reputation_data: list) -> Dict[str, Any]:
        if not self.api_key:
            return {"risk_score": 50, "analysis": "skipped (no key)", "flags": []}

        prompt = self._build_prompt(company_name, layer1_data, reputation_data)
        
        errors = []
        
        # reduced fallback - only try 2 models with 2 strategies each (max 4 calls)
        fast_models = ["gemini-2.0-flash", "gemini-1.5-flash"]
        tool_configs = [
            ("google_search", [{"google_search": {}}]),
            ("standard_llm", None)
        ]

        for model_name in fast_models:
            for tool_name, tools in tool_configs:
                try:
                    logger.info(f"trying gemini model: {model_name} with {tool_name}")
                    
                    if tools:
                        model = genai.GenerativeModel(model_name, tools=tools)
                    else:
                        model = genai.GenerativeModel(model_name)
                    
                    # timeout via generation config
                    resp = model.generate_content(
                        prompt,
                        request_options={"timeout": 30}
                    )
                    return self._parse_json(resp.text)
                except Exception as e:
                    err_msg = f"{model_name}({tool_name}): {str(e)[:100]}" 
                    errors.append(err_msg)
                    continue
        
        logger.error("all gemini models failed")
        return {
            "trust_score": 0, 
            "classification": "Unknown", 
            "analysis": f"ai analysis failed: {'; '.join(errors[:2])}...",
            "flags": ["AI_ERROR"]
        }

    def _generate_with_fallback(self, prompt: str) -> Dict[str, Any]:
        errors = []
        for model_name in self.models:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                return self._parse_json(resp.text)
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue
        
        logger.error(f"All extraction models failed: {errors}")
        return {}

    def extract_company_input(self, raw_text: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}

        prompt = f"""
        Extract company registration details from the following text into a JSON object.
        Focus on: Company Legal Name, Country of Registration, Industry, Registry ID (CIN/EIN), Website, LinkedIn, HR Name, HR Email, Address.
        
        TEXT:
        {raw_text[:4000]}
        
        OUTPUT JSON Schema:
        {{
            "name": "str (Legal Name)",
            "industry": "str",
            "country": "str (Country of Registration)",
            "registry_id": "str (or null)",
            "website_urls": ["str"],
            "linkedin_url": "str (or null)",
            "hr_name": "str (or null)",
            "hr_email": "str (or null)",
            "registered_address": "str (or null)"
        }}
        """
        
        data = self._generate_with_fallback(prompt)
        if not data:
            return {}

        if "website_urls" in data and isinstance(data["website_urls"], str):
            data["website_urls"] = [data["website_urls"]]
        
        required = ["name", "country", "hr_name", "hr_email"]
        missing = [f for f in required if not data.get(f)]
            
        if missing:
            logger.warning(f"Registration Document Rejected. Missing: {missing}")
            data["error"] = f"Invalid Registration Document. Missing: {', '.join(missing)}"
        
        return data

    def extract_offer_details(self, raw_text: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}

        prompt = f"""
        Analyze this text as a "Job Offer Letter" or "Internship Offer".
        
        STRICTLY EXTRACT:
        1. Company Legal Name
        2. Country (Infer from address if needed)
        3. HR/Signatory Name
        4. HR/Sender Email (CRITICAL)
        5. Role/Title Offered
        6. Stipend/Salary
        
        TEXT:
        {raw_text[:4000]}
        
        OUTPUT JSON Schema:
        {{
            "name": "str",
            "country": "str",
            "hr_name": "str",
            "hr_email": "str",
            "role": "str",
            "stipend_mentioned": "bool",
            "is_offer_letter": "bool",
            "missing_fields": ["str"]
        }}
        """
        
        data = self._generate_with_fallback(prompt)
        if not data:
            return {"error": "AI Extraction Failed"}

        required = ["name", "country", "hr_name", "hr_email", "role"]
        missing = [f for f in required if not data.get(f)]
        
        if missing or not data.get("is_offer_letter"):
            logger.warning(f"Offer Letter Rejected. Missing: {missing}")
            data["error"] = f"Invalid Offer Letter. Missing: {', '.join(missing)}"
        
        return data

    def verify_internship_relevance(self, raw_text: str, student_context: str) -> Dict[str, Any]:
        """
        verifies if the internship description is relevant to the student's programme/subjects.
        """
        if not self.api_key:
            return {}

        prompt = f"""
        act as an academic internship coordinator. 
        determine if the identified internship role and tasks are academically relevant for a student studying: "{student_context}".

        offer letter text:
        {raw_text[:4000]}

        task:
        1. identify the job role and key responsibilities from the text.
        2. compare them against the curriculum and career paths of the subjects in the student's programme (e.g. if "{student_context}" includes 'statistics', then data analyst roles are relevant).
        3. strictly filter out:
           - completely irrelevant roles (e.g. "social media marketing" for a physics student).
           - generic non-technical roles (e.g. "campus ambassador", "data entry").
           - mlm/pyramid scheme type roles.

        output json:
        {{
            "is_relevant": bool,
            "confidence_score": float (0-100),
            "reasoning": "brief explanation of why it fits or does not fit the programme/subjects.",
            "detected_role": "str"
        }}
        """
        
        return self._generate_with_fallback(prompt)

    def match_guide(self, student_json: Dict[str, Any], faculty_list: list) -> Dict[str, Any]:
        """
        matches a student to the best faculty based on internship description vs expertise.
        """
        if not self.api_key:
            return {}

        prompt = f"""
        Act as an Academic Internship Coordinator. Match the student to the best faculty guides based on expertise.

        STUDENT INTERNSHIP:
        Role: {student_json.get('internship_role')}
        Description: {student_json.get('internship_description')}
        Skills: {student_json.get('skills')}

        AVAILABLE FACULTY CANDIDATES:
        {json.dumps(faculty_list, indent=2)}

        TASK:
        1. Compare the Student's "Internship Description" with each Faculty's "Expertise".
        2. Select the TOP 3 most suitable faculty members.
        3. Assign an Expertise Score (0-100) for each.
           - >80: Perfect Match (Direct expertise alignment).
           - 60-80: Good Match (Related field).
           - <60: Weak Match.

        OUTPUT JSON:
        {{
            "ranked_matches": [
                {{
                    "faculty_id": "str",
                    "faculty_name": "str",
                    "expertise_score": float,
                    "reasoning": "brief explanation"
                }}
            ]
        }}
        """

        return self._generate_with_fallback(prompt)

    def _build_prompt(self, name: str, l1: Dict[str, Any], rep: list) -> str:
        signals = l1.get('signals', {})
        hr = l1.get('hr_data', {})
        addr = l1.get('address_data', {})
        
        return f"""
        act as fraud analyst. check '{name}'.
        
        You have access to Google Search. USE IT.
        Perform independent verification to confirm:
        1. Company existence and official website.
        2. Recent news or regulatory warnings.
        3. Employee presence on LinkedIn.
        
        PROVIDED DATA (Layer 1):
        - Industry: {l1.get('industry') or 'Not Provided'}
        - Registry Found: {signals.get('registry_link_found')}
        - HR Verification: {signals.get('hr_verified')} (Name: {hr.get('name')})
        - Address Verification: {signals.get('address_verified')} (Input: {addr.get('input') or 'Not Provided'})
        - Digital Footprint: LinkedIn={signals.get('linkedin_verified')}, Website={signals.get('website_content_match')}
        - PDL Profile: {json.dumps(l1.get('pdl_data', {}), default=str)}
        - Reviews/Scam Search (Prelim): {json.dumps(rep[:5])}

        TASK: report legitimacy.
        1. Calculate Trust Score (0-100).
        2. Classify into: "High Trust", "Review Needed", "Low Trust".
        3. Analysis must cite findings from YOUR Google Search.
        
        OUTPUT JSON: {{ "trust_score": int, "classification": "str", "analysis": "str", "flags": ["str"] }}
        """

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            # clean markdown
            clean = text.replace("```json", "").replace("```", "").strip()
            # handle text before json
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start != -1 and end != -1:
                clean = clean[start:end]
            return json.loads(clean)
        except:
            return {"trust_score": 0, "classification": "Error", "analysis": text[:100], "flags": ["PARSE_ERROR"]}
