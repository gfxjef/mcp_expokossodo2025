"""
Redis client for caching
"""
import json
import asyncio
from typing import Optional, Any
from datetime import datetime, timedelta
import aioredis
import structlog

from app.config import settings

logger = structlog.get_logger()


class RedisCache:
    """Redis cache client"""
    
    def __init__(self):
        self.redis = None
        self.connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            await self.redis.ping()
            self.connected = True
            logger.info("redis_connected", url=settings.redis_url)
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e))
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("redis_disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.connected:
            return None
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning("cache_get_error", key=key, error=str(e))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.connected:
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            # Set with TTL
            if ttl_seconds:
                await self.redis.setex(key, ttl_seconds, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            
            return True
        except Exception as e:
            logger.warning("cache_set_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.connected:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning("cache_delete_error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.connected:
            return False
        
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.warning("cache_exists_error", key=key, error=str(e))
            return False


# Global cache instance
cache = RedisCache()


async def get_cache_key(tool_name: str, **params) -> str:
    """Generate cache key for tool"""
    # Remove None values and sort for consistent keys
    filtered_params = {k: v for k, v in params.items() if v is not None}
    sorted_params = sorted(filtered_params.items())
    params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
    return f"mcp:{tool_name}:{params_str}"


# TTL configurations (in seconds)
CACHE_TTL = {
    "mapaSalaEvento": 60,        # 1 minute - hot resource
    "getAforo": 60,              # 1 minute - changes frequently
    "getEventos": 300,           # 5 minutes - moderately stable
    "getInscritos": 600,         # 10 minutes - less frequent changes
    "getEstadisticas": 300,      # 5 minutes - expensive calculations
    # No cache for writes and searches
    "confirmarAsistencia": 0,
    "buscarRegistro": 0
}


async def cache_get(tool_name: str, **params) -> Optional[Any]:
    """Get from cache with tool-specific logic"""
    if CACHE_TTL.get(tool_name, 0) == 0:
        return None
    
    key = await get_cache_key(tool_name, **params)
    return await cache.get(key)


async def cache_set(tool_name: str, value: Any, **params) -> bool:
    """Set in cache with tool-specific TTL"""
    ttl = CACHE_TTL.get(tool_name, 0)
    if ttl == 0:
        return False
    
    key = await get_cache_key(tool_name, **params)
    return await cache.set(key, value, ttl)


# Initialize cache connection
async def init_cache():
    """Initialize cache connection"""
    await cache.connect()


# Cleanup cache connection
async def close_cache():
    """Close cache connection"""
    await cache.disconnect()