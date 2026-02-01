import asyncio
import sys
import os
import logging

# add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.redis import redis_client

# setup logging
logging.basicConfig(level=logging.INFO)

async def test_redis():
    print("\n--- Testing Redis Connection ---")
    try:
        # 1. Connect
        await redis_client.connect()
        
        # 2. Write
        test_key = "test_verification_id"
        test_val = "verified_cached_data"
        print(f"Setting Key: {test_key} -> {test_val}")
        await redis_client.set(test_key, test_val, ttl=60)
        
        # 3. Read
        print("Reading Key...")
        val = await redis_client.get(test_key)
        print(f"Got Value: {val}")
        
        if val == test_val:
            print("SUCCESS: Redis is working correctly!")
        else:
            print("FAILURE: Value mismatch or None returned.")
            
        await redis_client.close()
        
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_redis())
