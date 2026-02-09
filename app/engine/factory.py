import os
from app.engine.gemini_provider import GeminiProvider

def get_ai_provider():
    """factory to return ai provider. defaults to gemini."""
    provider_type = os.getenv("AI_PROVIDER", "gemini").lower()
    
    if provider_type == "slm":
        pass
        
    return GeminiProvider()
