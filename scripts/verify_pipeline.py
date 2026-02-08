import sys
import os
import time
import subprocess
import httpx
import logging
import json

# configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger()

def run_verification():
    server = None
    try:
        logger.info("initializing verification sequence...")
        
        # start server
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # wait for boot
        time.sleep(10)
        
        base_url = "http://127.0.0.1:8001"
        key = os.getenv("API_ACCESS_KEY", "test-key")
        headers = {"Legitimacy-engine-key": key}

        # 1. health check
        try:
            r = httpx.get(f"{base_url}/")
            if r.status_code == 200:
                logger.info("health check: pass")
            else:
                logger.error(f"health check: fail ({r.status_code})")
        except Exception:
            logger.error("health check: connection refused")
            return

        # 2. company verification
        payload = {
            "name": "Tata Consultancy Services",
            "country": "India", 
            "hr_name": "Rajesh Gopinathan",
            "hr_email": "rajesh@tcs.com",
            "website_urls": ["https://www.tcs.com"],
            "user_id": "verify-test-user"
        }
        try:
            r = httpx.post(f"{base_url}/verification/verify", json=payload, headers=headers, timeout=60.0)
            if r.status_code == 200:
                data = r.json()
                logger.info(f"verification: pass (score={data.get('trust_score')})")
            else:
                logger.error(f"verification: fail ({r.status_code})")
                logger.error(r.text)
        except Exception as e:
            logger.error(f"verification: error ({e})")

        # 3. allocation check
        alloc_payload = {
            "student": {
                "id": "s1", "name": "student_test", "internship_role": "dev", 
                "internship_description": "python dev", "skills": ["python"]
            },
            "available_faculty": [
                {"id": "f1", "name": "prof_test", "department": "cs", "expertise": ["python"], "current_load": 0}
            ]
        }
        try:
            r = httpx.post(f"{base_url}/verification/allocation/recommend", json=alloc_payload, headers=headers)
            if r.status_code == 200:
                logger.info("allocation: pass")
            else:
                logger.error(f"allocation: fail ({r.status_code})")
        except Exception as e:
            logger.error(f"allocation: error ({e})")

    finally:
        logger.info("terminating sequence...")
        if server:
            server.terminate()
            if sys.platform == 'win32':
                 subprocess.call(['taskkill', '/F', '/T', '/PID', str(server.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_verification()
