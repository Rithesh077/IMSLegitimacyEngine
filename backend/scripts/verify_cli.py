import sys
import os
import asyncio
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.pipeline_orchestrator import PipelineOrchestrator
from app.schemas.company import CompanyInput
from app.core.redis import redis_client

# Configure simplified logging output
logging.basicConfig(level=logging.INFO, format='%(message)s')

async def main():
    print("\n=== Company Legitimacy Verification Tool (CLI) ===")
    print("Type 'exit' or 'quit' to terminate the session.\n")

    # Connect to Redis
    try:
        await redis_client.connect()
    except Exception as e:
        print(f"Warning: Redis connection failed ({e}). Caching will be disabled.")

    orchestrator = PipelineOrchestrator()

    while True:
        try:
            name = input("\nCompany Name: ").strip()
            if name.lower() in ['exit', 'quit']:
                print("Exiting...")
                break
            if not name:
                print("Error: Company name is required.")
                continue

            country = input("Country (e.g. India, USA): ").strip()
            if not country:
                print("Error: Country is required.")
                continue

            reg_id = input("Registration ID (Mandatory): ").strip()
            if not reg_id:
                print("Error: Registration ID is mandatory for verification.")
                continue

            # Optional inputs
            linkedin = input("LinkedIn URL (Optional): ").strip() or None
            
            websites_input = input("Website(s) (Optional, comma separated): ").strip()
            website_urls = [u.strip() for u in websites_input.split(',')] if websites_input else []

            print(f"\nProcessing signals for '{name}' in '{country}'...")
            
            company_input = CompanyInput(
                name=name, 
                country=country, 
                registry_id=reg_id, 
                linkedin_url=linkedin,
                website_urls=website_urls
            )
            
            result = await orchestrator.run_pipeline(company_input)

            print("\n--- Verification Results ---")
            print(f"Status:      {result.verification_status}")
            print(f"Trust Score: {result.trust_score}/100")
            print(f"Tier:        {result.trust_tier}")
            
            if result.details and "signals" in result.details:
                print("\n[Signal Checklist]")
                signals = result.details["signals"]
                
                print("[Registry Sources]")
                breakdown = signals.get("registry_breakdown", {})
                if breakdown:
                    for domain, found in breakdown.items():
                        mark = "VERIFIED" if found else "NOT FOUND"
                        print(f"  - {domain}: {mark}")
                else:
                    reg_mark = "YES" if signals.get("registry_link_found") else "NO"
                    print(f"  - Global Link: {reg_mark}")
                
                print("\n[Additional Signals]")
                if linkedin:
                    li_mark = "VERIFIED" if signals.get("linkedin_verified") else "NOT VERIFIED"
                    print(f"  - LinkedIn:     {li_mark}")
                
                if website_urls:
                    web_mark = "VERIFIED" if signals.get("website_content_match") else "NOT VERIFIED"
                    print(f"  - Website:      {web_mark}")

            print("-" * 30)

        except KeyboardInterrupt:
            print("\nSession Terminated.")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Close Redis connection on exit
    await redis_client.close()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
