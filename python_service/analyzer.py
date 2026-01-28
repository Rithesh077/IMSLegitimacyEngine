from transformers import pipeline

# Load pipeline once globally to avoid reloading on every request
# Using a distilled model for speed/memory efficiency
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def analyze_credibility(scraped_data):
    reviews = scraped_data.get("reviews", [])
    
    if not reviews:
        return {
            "trust_score": 50, # Neutral
            "trust_tier": "MEDIUM", 
            "details": "No online reviews found."
        }
        
    positive_count = 0
    negative_count = 0
    total_score = 0
    
    for review in reviews:
        # returns [{ 'label': 'POSITIVE', 'score': 0.99 }]
        result = sentiment_pipeline(review[:512])[0] # Truncate to 512 tokens
        
        if result['label'] == 'POSITIVE':
            positive_count += 1
            total_score += result['score']
        else:
            negative_count += 1
            total_score -= result['score']
            
    # Calculate Final Score (0 to 100)
    # Simple heuristic: Ratio of positive to total
    total_reviews = len(reviews)
    ratio = positive_count / total_reviews
    final_score = int(ratio * 100)
    
    tier = "MEDIUM"
    if final_score > 80: tier = "HIGH"
    if final_score < 40: tier = "LOW"
    
    return {
        "trust_score": final_score,
        "trust_tier": tier,
        "review_count": total_reviews,
        "sources": scraped_data.get("sources_found", [])
    }
