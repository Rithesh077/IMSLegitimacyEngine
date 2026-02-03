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
        
        for model_name in self.models:
            try:
                logger.info(f"trying gemini model: {model_name}")
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                return self._parse_json(resp.text)
            except Exception as e:
                logger.warning(f"model {model_name} failed: {e}")
                continue
        
        logger.error("all gemini models failed")
        logger.error("all gemini models failed")
        return {"trust_score": 0, "classification": "Unknown", "analysis": "AI analysis failed (all models)", "flags": ["AI_ERROR"]}

    def _build_prompt(self, name: str, l1: Dict[str, Any], rep: list) -> str:
        signals = l1.get('signals', {})
        hr = l1.get('hr_data', {})
        addr = l1.get('address_data', {})
        
        return f"""
        act as fraud analyst. check '{name}'.
        
        DATA:
        - Industry: {l1.get('industry') or 'Not Provided'}
        - Registry Found: {signals.get('registry_link_found')}
        - HR Verification: {signals.get('hr_verified')} (Name: {hr.get('name')})
        - Address Verification: {signals.get('address_verified')} (Input: {addr.get('input') or 'Not Provided'})
        - Digital Footprint: LinkedIn={signals.get('linkedin_verified')}, Website={signals.get('website_content_match')}
        - PDL Profile: {json.dumps(l1.get('pdl_data', {}), default=str)}
        - Reviews/Scam Search: {json.dumps(rep[:5])}

        TASK: report legitimacy.
        1. Calculate Trust Score (0-100).
        2. Classify into: "High Trust", "Review Needed", "Low Trust".
        NOTE: High trust if HR/Address are verified even if Registry is missing.

        OUTPUT JSON: {{ "trust_score": int, "classification": "str", "analysis": "str", "flags": ["str"] }}
        """

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            return {"trust_score": 0, "classification": "Error", "analysis": text[:100], "flags": ["PARSE_ERROR"]}
