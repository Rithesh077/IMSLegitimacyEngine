import os
from app.engine.gemini_provider import GeminiProvider

def get_ai_provider():
    """
    factory to return the appropriate ai/slm provider.
    currently defaults to geminiprovider.
    future: can switch based on env var ai_provider="slm".
    """
    provider_type = os.getenv("AI_PROVIDER", "gemini").lower()
    
    if provider_type == "slm":
        # return SLMProvider()
        pass
        
    return GeminiProvider()       
