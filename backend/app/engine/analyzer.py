from transformers import pipeline
from app.schemas.company import VerificationResult, CredibilityAnalysis
from typing import Dict, Any

# Load pipeline once globally to avoid reloading on every request
# Using a distilled model for speed/memory efficiency (approx 260MB download)
try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
except Exception as e:
    print(f"WARNING: Transformer model failed to load: {e}")
    sentiment_pipeline = None

def analyze_credibility(verification_result: VerificationResult, scraped_data: Dict[str, Any]) -> CredibilityAnalysis:
    """
    Combines Official Registry Data + Scraped Public Sentiment to calculate a Trust Score.
    """
    # registry score is the base
    base_score = verification_result.confidence_score
    red_flags = verification_result.red_flags.copy() # copy to avoid mutating original

    # analyze scraped content
    sources = scraped_data.get("sources", [])
    
    if not sources:
        # fallback if no web data found
        return CredibilityAnalysis(
            trust_score=base_score,
            trust_tier=_get_tier(base_score),
            verification_status=verification_result.status,
            review_count=0,
            sentiment_summary="no public sources found",
            red_flags=red_flags,
            scraped_sources=[],
            details={"note": "analysis based primarily on registry data"}
        )
        
    positive_count = 0
    negative_count = 0
    sentiment_adjustment = 0
    
    if sentiment_pipeline:
        for source in sources:
            text = source.get("text", "")
            if len(text) < 50: continue
                
            # analyze chunks of text (truncating to 512 chars for now)
            try:
                result = sentiment_pipeline(text[:512])[0] 
                
                if result['label'] == 'POSITIVE':
                    positive_count += 1
                    sentiment_adjustment += 5 # bonus for positive coverage
                elif result['label'] == 'NEGATIVE':
                    negative_count += 1
                    sentiment_adjustment -= 10 # penalty for negative coverage is higher
            except Exception:
                continue
            
    # cap adjustment (-50 to +50)
    sentiment_adjustment = max(-50, min(50, sentiment_adjustment))
    
    # calculate final score
    final_score = base_score + sentiment_adjustment
    final_score = max(0, min(100, final_score)) # clamp 0-100
    
    return CredibilityAnalysis(
        trust_score=final_score,
        trust_tier=_get_tier(final_score),
        verification_status=verification_result.status,
        review_count=len(sources),
        sentiment_summary=f"Positive Signals: {positive_count}, Negative Signals: {negative_count}",
        red_flags=red_flags,
        scraped_sources=[s['url'] for s in sources],
        details={
            "base_registry_score": base_score,
            "sentiment_adjustment": sentiment_adjustment
        }
    )

def _get_tier(score: float) -> str:
    if score >= 80: return "HIGH"
    if score >= 50: return "MEDIUM"
    return "LOW"
