import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis_client = None
_memory_cache = {}

def _get_redis():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()
                logger.info("redis connected")
            except Exception as e:
                logger.warning(f"redis unavailable, using memory: {e}")
                _redis_client = False
        else:
            _redis_client = False
    return _redis_client if _redis_client else None

def cache_get(key: str) -> Optional[dict]:
    """get from redis, fallback to memory only if redis unavailable."""
    r = _get_redis()
    if r:
        try:
            val = r.get(key)
            if val:
                logger.info(f"redis hit: {key[:16]}")
                return json.loads(val)
        except Exception as e:
            logger.warning(f"redis error: {e}")
    elif key in _memory_cache:
        logger.info(f"memory hit: {key[:16]}")
        return _memory_cache[key]
    return None

def cache_set(key: str, value: dict, ttl: int = 86400) -> None:
    """set in redis, fallback to memory only if redis unavailable."""
    r = _get_redis()
    if r:
        try:
            r.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"redis error: {e}")
            _memory_cache[key] = value
    else:
        _memory_cache[key] = value

def cache_clear() -> None:
    global _memory_cache
    _memory_cache = {}
    r = _get_redis()
    if r:
        try:
            r.flushdb()
        except:
            pass
