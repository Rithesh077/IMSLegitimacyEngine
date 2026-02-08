import sys
import os
import json

# Add parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock env vars to prevent startup crashes if .env is missing/invalid during export
# This ensures the script runs even in a minimal environment
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://mock:mock@localhost/mockdb"
if "API_ACCESS_KEY" not in os.environ:
    os.environ["API_ACCESS_KEY"] = "mock-access-key"
if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = "mock-gemini-key"

try:
    from app.main import app
except Exception as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

def export():
    print("generating openapi schema...")
    try:
        openapi_data = app.openapi()
        
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        output_path = os.path.join(docs_dir, "openapi.json")
        
        with open(output_path, "w") as f:
            json.dump(openapi_data, f, indent=2)
            
        print(f"openapi schema exported to: {output_path}")
        print("backend team can import this file into postman or swagger ui for easy testing.")
        
    except Exception as e:
        print(f"failed to export schema: {e}")

if __name__ == "__main__":
    export()
