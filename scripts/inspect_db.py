import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Load env variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env")
    print("Please add it: DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname")
    exit(1)

async def inspect_schema():
    print(f"Connecting to: {DATABASE_URL.split('@')[-1]}...") # Hide creds
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            # list tables
            print("\n--- TABLES ---")
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = result.fetchall()
            
            if not tables:
                print("No tables found in 'public' schema.")
            
            for (table_name,) in tables:
                print(f"- {table_name}")
                
                # list columns for each table
                cols = await conn.execute(text(
                    f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"
                ))
                for col_name, dtype in cols:
                    print(f"    - {col_name}: {dtype}")
                
        print("\nInspection Complete.")
        
    except Exception as e:
        print(f"\nConnection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_schema())
