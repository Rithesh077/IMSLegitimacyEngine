import redis.asyncio as redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisClient:
    """
    async redis client wrapper
    handles connection and basic get/set operations
    defaults to localhost:6379 for local dev
    """
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._host = os.getenv("REDIS_HOST", "localhost")
        self._port = int(os.getenv("REDIS_PORT", 6379))
        self._password = os.getenv("REDIS_PASSWORD", None)

    async def connect(self):
        """
        establishes connection pool
        """
        try:
            self._redis = redis.Redis(
                host=self._host,
                port=self._port,
                password=self._password,
                decode_responses=True, # returns strings instead of bytes
                socket_timeout=5.0
            )
            # ping to verify connection
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self._host}:{self._port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
            raise e

    async def get(self, key: str) -> Optional[str]:
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        if not self._redis:
            return False
        try:
            return await self._redis.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def rpush(self, key: str, value: str) -> bool:
        if not self._redis:
            return False
        try:
            await self._redis.rpush(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis RPUSH error: {e}")
            return False

    async def lpop(self, key: str) -> Optional[str]:
        if not self._redis:
            return None
        try:
            return await self._redis.lpop(key)
        except Exception as e:
            logger.error(f"Redis LPOP error: {e}")
            return None

    async def close(self):
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

# global instance
redis_client = RedisClient()
