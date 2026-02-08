import secrets
import os
import re

def generate_and_save():
    key = secrets.token_urlsafe(32)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        
        # replace existing key or append
        if "API_ACCESS_KEY=" in content:
            content = re.sub(r"API_ACCESS_KEY=.*", f"API_ACCESS_KEY={key}", content)
        else:
            content = content.rstrip() + f"\nAPI_ACCESS_KEY={key}\n"
        
        with open(env_path, "w") as f:
            f.write(content)
    else:
        with open(env_path, "w") as f:
            f.write(f"API_ACCESS_KEY={key}\n")
    
    print("api access key updated in .env")
    print("remember to update render environment if deploying!")

if __name__ == "__main__":
    generate_and_save()
