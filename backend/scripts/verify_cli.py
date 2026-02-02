import sys
import os
import asyncio
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# ... (keep load_dotenv blocks)

# ...

async def main():
    print("\n=== company legitimacy verification cli ===")
    print("type 'exit' to quit.\n")

    # connect redis
    try: await redis_client.connect()
    except Exception as e:
        print(f"warn: redis failed ({e}). caching disabled.")

    orchestrator = PipelineOrchestrator()

    while True:
        try:
            name = input("\ncompany name: ").strip()
            if name.lower() in ['exit', 'quit']: break
            if not name: continue

            # TODO: parse document for auto-verification logic place here
            # doc_path = input("path to doc (optional): ")

            country = input("country (default: india): ").strip() or "India"
            reg_id = input("registration id (mandatory): ").strip()
            if not reg_id:
                print("error: id required")
                continue

            linkedin = input("linkedin url (optional): ").strip()
            website = input("website (optional): ").strip()

            print(f"processing '{name}'...")
            
            company_input = CompanyInput(
                name=name,country=country,
                registry_id=reg_id,
                linkedin_url=linkedin or None,
                website_urls=[website] if website else None
            )
            
            result = await orchestrator.run_pipeline(company_input)
            
            # --- results ---
            det = result.details
            pdl = det.get("pdl_data", {})
            
            print("\n" + "="*60)
            print(f"analysis: {name.upper()}")
            print("="*60)
            
            print(f"{'FIELD':<20} | {'INPUT':<30} | {'PDL':<30}")
            print("-" * 86)
            print(f"{'Name':<20} | {name[:28]:<30} | {pdl.get('name', 'N/A')[:28]:<30}")
            print(f"{'Location':<20} | {country:<30} | {str(pdl.get('location', {}).get('country', 'N/A'))[:28]:<30}")
            print("-" * 86)

            matches = det.get("match_details", {})
            print(f"\nscores:")
            print(f"  - search: {matches.get('input_vs_search_score')}/100")
            print(f"  - pdl:    {matches.get('input_vs_pdl_score')}/100")
            
            print(f"\nstatus: {result.verification_status} (score: {result.trust_score})")
            print("="*60)

            # --- admin ---
            final = result.verification_status
            while True:
                c = input("\nadmin [c]onfirm / [o]verride / [r]eject: ").lower()
                if c == 'c': break
                elif c == 'o': final = "Verified"; print("overridden."); break
                elif c == 'r': final = "Rejected"; print("rejected."); break
            
            # --- queue ---
            payload = {
                "name": name, "status": final, "score": result.trust_score,
                "details": det, "ts": datetime.utcnow().isoformat()
            }
            
            try:
                if await redis_client.rpush("queue:sentiment_analysis", json.dumps(payload)):
                    print("[ok] queued")
                else:
                    print("[warn] redis offline. skip.")
            except Exception as e:
                print(f"[err] queue: {e}")
                
            print("-" * 30)

        except KeyboardInterrupt: break
        except Exception as e:
            print(f"\n[err] {e}")

    await redis_client.close()
    print("\nbye.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
