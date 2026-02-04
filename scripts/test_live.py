import httpx
import asyncio
import json

async def test_live_verification():
    url = "http://localhost:8001/verification/verify"
    
    payload = {
        "name": "Zerodha Broking Limited",
        "country": "India",
        "hr_name": "Venu Madhav",
        "hr_email": "venu.madhav@zerodha.com",
        "industry": "Fintech",
        "website_urls": ["https://zerodha.com"]
    }
    
    print(f"Testing {url}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            
        print(f"\nStatus Level: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("\n--- PASSED ---")
            print(f"Trust Score: {data.get('trust_score')}")
            print(f"Status: {data.get('verification_status')}")
            print(f"Classification: {data.get('trust_tier')}")
            print(f"AI Summary: {data.get('sentiment_summary')}")
            
            import os
            os.makedirs("outputs", exist_ok=True)
            with open("outputs/output.json", "w") as f:
                json.dump(data, f, indent=2)
            print("\n[i] Full output saved to 'outputs/output.json'")
        else:
            print("\n--- FAILED ---")
            print(resp.text)
            
    except Exception as e:
        print(f"\nError: Is the server running? ({e})")

if __name__ == "__main__":
    asyncio.run(test_live_verification())
