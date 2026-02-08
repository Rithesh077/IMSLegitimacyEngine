import sys
import os
import time
import subprocess
import httpx
import logging
import json

# strict logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger()

def run_paranoid_check():
    # load env vars explicitly
    from dotenv import load_dotenv
    load_dotenv()
    
    server = None
    try:
        logger.info("[1/5] starting server...")
        
        # force kill any existing instance
        if sys.platform == 'win32':
             subprocess.call(['taskkill', '/F', '/IM', 'uvicorn.exe'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # pass current env (with loaded variables) to server process
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env=os.environ
        )
        
        # longer wait for safe boot
        time.sleep(12)
        
        base_url = "http://127.0.0.1:8001"
        raw_key = os.getenv("API_ACCESS_KEY", "test-key")
        key = raw_key.strip()
        
        if key == "test-key":
             logger.warning("warning: using default 'test-key'. ensure API_ACCESS_KEY is set in .env")
        else:
             logger.info(f"using key: {key[:4]}*** (len={len(key)})")
             
        headers = {"Legitimacy-engine-key": key}

        # 2. auth check (negative test)
        logger.info("[2/5] checking security...")
        try:
            r = httpx.post(f"{base_url}/verification/verify", json={}, headers={"Legitimacy-engine-key": "bad-key"})
            if r.status_code == 403:
                logger.info("security: active (403 received)")
            else:
                logger.error(f"security breach: {r.status_code}")
                return
        except Exception:
            logger.error("security check failed")
            return

        # 3. full verification flow
        logger.info("[3/5] running full pipeline (tata consultancy services)...")
        payload = {
            "name": "Tata Consultancy Services",
            "country": "India", 
            "hr_name": "Rajesh Gopinathan",
            "hr_email": "rajesh.g@tcs.com",
            "website_urls": ["https://www.tcs.com"],
            "linkedin_url": "https://www.linkedin.com/company/tata-consultancy-services",
            "user_id": "paranoid-test-user-001"
        }
        try:
            start_time = time.time()
            r = httpx.post(f"{base_url}/verification/verify", json=payload, headers=headers, timeout=90.0)
            duration = time.time() - start_time
            
            if r.status_code == 200:
                data = r.json()
                score = data.get('trust_score')
                logger.info(f"pipeline success ({duration:.2f}s)")
                logger.info(f"trust score: {score}")
                if score < 50:
                    logger.warning(f"warning: low score for legit company ({score})")
            else:
                logger.error(f"pipeline failed ({r.status_code})")
                logger.error(r.text)
        except Exception as e:
            logger.error(f"pipeline exception: {e}")

        # 4. persistence check
        logger.info("[4/5] checking database persistence...")
        try:
            r = httpx.get(f"{base_url}/verification/history", headers=headers)
            if r.status_code == 200:
                history = r.json().get('history', [])
                found = any(h.get('Company Name') == "Tata Consultancy Services" for h in history)
                if found:
                    logger.info("db persistence: confirmed")
                else:
                    logger.warning("db persistence: record not found in history logs (check excel logger)")
            else:
                logger.error(f"history endpoint failed ({r.status_code})")
        except Exception as e:
            logger.error(f"persistence check error: {e}")

        # 5. allocation logic
        logger.info("[5/5] checking allocation logic...")
        alloc_payload = {
            "student": {
                "id": "s_paranoid", "name": "Deep Learner", "internship_role": "AI Researcher", 
                "internship_description": "deep learning neural networks", "skills": ["pytorch", "python"]
            },
            "available_faculty": [
                {"id": "f_web", "name": "Prof Web", "department": "cs", "expertise": ["react", "node"], "current_load": 0},
                {"id": "f_ai", "name": "Prof AI", "department": "cs", "expertise": ["deep learning", "nlp"], "current_load": 0}
            ]
        }
        try:
            r = httpx.post(f"{base_url}/verification/allocation/recommend", json=alloc_payload, headers=headers)
            if r.status_code == 200:
                rec = r.json()
                if rec.get('recommended_faculty_id') == "f_ai":
                    logger.info(f"allocation logic: correct (picked {rec.get('faculty_name')})")
                else:
                    logger.error(f"allocation logic: incorrect (picked {rec.get('faculty_name')})")
            else:
                logger.error(f"allocation failed ({r.status_code})")
        except Exception as e:
            logger.error(f"allocation error: {e}")

    finally:
        logger.info("shutting down...")
        if server:
            server.terminate()
            if sys.platform == 'win32':
                 subprocess.call(['taskkill', '/F', '/T', '/PID', str(server.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_paranoid_check()
