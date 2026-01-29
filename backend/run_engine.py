import asyncio
from app.engine.scraper import scrape_company_data
from app.engine.registry_verifier import RegistryVerifier
from app.schemas.company import CompanyInput

async def run_pipeline():
    # inputs
    company_name = input("Enter Company Name: ")
    cin = input("Enter CIN (Optional, press Enter to skip): ") or None
    
    input_data = CompanyInput(name=company_name, cin=cin)
    
    # registry check
    print("\nverifying registry...")
    verifier = RegistryVerifier()
    verification_result = verifier.verify_company(input_data)
    print(f"status: {verification_result.status}")
    print(f"confidence: {verification_result.confidence_score}")

    # scraping
    if verification_result.can_proceed_to_scraping:
        print("\nscraping web...")
        scraped_data = await scrape_company_data(company_name, cin)
        print(f"found {scraped_data['scraped_sources_count']} sources")
        for source in scraped_data['sources']:
            print(f"- {source['title']} ({source['url']})")
    else:
        print("\nskipping scraping")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
