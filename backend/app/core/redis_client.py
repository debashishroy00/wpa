"""
WealthPath AI - Redis Client Configuration
"""
import redis
from typing import Optional, Union, Any
import json
import structlog
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings

logger = structlog.get_logger()


class RedisClient:
    """
    Redis client wrapper for WealthPath AI
    """
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None
    
    def connect(self):
        """
        Initialize Redis connection
        """
        try:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            self.client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            self.client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise e
    
    def disconnect(self):
        """
        Close Redis connection
        """
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
    
    def set(
        self, 
        key: str, 
        value: Union[str, int, dict, list], 
        expire: Optional[int] = None
    ) -> bool:
        """
        Set a key-value pair in Redis
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = self.client.set(key, value, ex=expire)
            logger.debug("Redis SET", key=key, expire=expire)
            return result
        
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Redis
        """
        try:
            value = self.client.get(key)
            if value is None:
                return default
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return default
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis
        """
        try:
            result = self.client.delete(*keys)
            logger.debug("Redis DELETE", keys=keys, deleted_count=result)
            return result
        
        except Exception as e:
            logger.error("Redis DELETE failed", keys=keys, error=str(e))
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis
        """
        try:
            return bool(self.client.exists(key))
        
        except Exception as e:
            logger.error("Redis EXISTS failed", key=key, error=str(e))
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key
        """
        try:
            result = self.client.expire(key, seconds)
            logger.debug("Redis EXPIRE", key=key, seconds=seconds)
            return result
        
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get time to live for a key
        """
        try:
            return self.client.ttl(key)
        
        except Exception as e:
            logger.error("Redis TTL failed", key=key, error=str(e))
            return -1
    
    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value
        """
        try:
            result = self.client.incrby(key, amount)
            logger.debug("Redis INCR", key=key, amount=amount, result=result)
            return result
        
        except Exception as e:
            logger.error("Redis INCR failed", key=key, error=str(e))
            return 0
    
    def hash_set(self, name: str, key: str, value: Union[str, int, dict, list]) -> bool:
        """
        Set a field in a hash
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = self.client.hset(name, key, value)
            logger.debug("Redis HSET", name=name, key=key)
            return bool(result)
        
        except Exception as e:
            logger.error("Redis HSET failed", name=name, key=key, error=str(e))
            return False
    
    def hash_get(self, name: str, key: str, default: Any = None) -> Any:
        """
        Get a field from a hash
        """
        try:
            value = self.client.hget(name, key)
            if value is None:
                return default
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        
        except Exception as e:
            logger.error("Redis HGET failed", name=name, key=key, error=str(e))
            return default
    
    def hash_get_all(self, name: str) -> dict:
        """
        Get all fields from a hash
        """
        try:
            result = self.client.hgetall(name)
            
            # Parse JSON values
            parsed_result = {}
            for key, value in result.items():
                try:
                    parsed_result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_result[key] = value
            
            return parsed_result
        
        except Exception as e:
            logger.error("Redis HGETALL failed", name=name, error=str(e))
            return {}
    
    def list_push(self, name: str, *values: Union[str, int, dict, list]) -> int:
        """
        Push values to a list
        """
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
            
            result = self.client.lpush(name, *serialized_values)
            logger.debug("Redis LPUSH", name=name, count=len(values))
            return result
        
        except Exception as e:
            logger.error("Redis LPUSH failed", name=name, error=str(e))
            return 0
    
    def list_pop(self, name: str, timeout: int = 0) -> Any:
        """
        Pop a value from a list
        """
        try:
            if timeout > 0:
                result = self.client.brpop(name, timeout=timeout)
                if result:
                    _, value = result
                else:
                    return None
            else:
                value = self.client.rpop(name)
            
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        
        except Exception as e:
            logger.error("Redis RPOP failed", name=name, error=str(e))
            return None
    
    def set_add(self, name: str, *values: Union[str, int]) -> int:
        """
        Add values to a set
        """
        try:
            result = self.client.sadd(name, *values)
            logger.debug("Redis SADD", name=name, count=len(values))
            return result
        
        except Exception as e:
            logger.error("Redis SADD failed", name=name, error=str(e))
            return 0
    
    def set_is_member(self, name: str, value: Union[str, int]) -> bool:
        """
        Check if value is in set
        """
        try:
            return bool(self.client.sismember(name, value))
        
        except Exception as e:
            logger.error("Redis SISMEMBER failed", name=name, error=str(e))
            return False
    
    def health_check(self) -> bool:
        """
        Check Redis health
        """
        try:
            self.client.ping()
            return True
        
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """
    Get Redis client instance
    """
    return redis_client


@asynccontextmanager
async def redis_context():
    """
    Redis context manager for connection lifecycle
    """
    try:
        redis_client.connect()
        yield redis_client
    finally:
        redis_client.disconnect()


# Session and caching utilities
class SessionManager:
    """
    Redis-based session management
    """
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.session_ttl = 7 * 24 * 60 * 60  # 7 days
    
    def create_session(self, session_id: str, user_id: int, data: dict) -> bool:
        """
        Create a new session
        """
        session_key = f"{self.session_prefix}{session_id}"
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        
        session_data = {
            "user_id": user_id,
            "created_at": json.dumps(datetime.now().isoformat()),
            **data
        }
        
        # Store session data
        success = self.redis.set(session_key, session_data, expire=self.session_ttl)
        if success:
            # Add session to user's session list
            self.redis.set_add(user_sessions_key, session_id)
            self.redis.expire(user_sessions_key, self.session_ttl)
        
        return success
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data
        """
        session_key = f"{self.session_prefix}{session_id}"
        return self.redis.get(session_key)
    
    def update_session(self, session_id: str, data: dict) -> bool:
        """
        Update session data
        """
        session_key = f"{self.session_prefix}{session_id}"
        existing_data = self.redis.get(session_key, {})
        
        if not existing_data:
            return False
        
        existing_data.update(data)
        return self.redis.set(session_key, existing_data, expire=self.session_ttl)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        """
        session_key = f"{self.session_prefix}{session_id}"
        session_data = self.redis.get(session_key)
        
        if session_data and "user_id" in session_data:
            user_sessions_key = f"{self.user_sessions_prefix}{session_data['user_id']}"
            # Remove from user's session list (this would need Redis set operations)
            # For now, we'll just delete the main session
        
        return bool(self.redis.delete(session_key))
    
    def delete_user_sessions(self, user_id: int) -> int:
        """
        Delete all sessions for a user
        """
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        # This would require implementing set operations in Redis client
        # For now, return 0
        return 0


# Cache utilities
class CacheManager:
    """
    Redis-based caching utilities
    """
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.cache_prefix = "cache:"
        self.default_ttl = 3600  # 1 hour
    
    def cache_key(self, namespace: str, key: str) -> str:
        """
        Generate cache key
        """
        return f"{self.cache_prefix}{namespace}:{key}"
    
    def set_cache(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set cache value
        """
        cache_key = self.cache_key(namespace, key)
        return self.redis.set(cache_key, value, expire=ttl or self.default_ttl)
    
    def get_cache(self, namespace: str, key: str, default: Any = None) -> Any:
        """
        Get cache value
        """
        cache_key = self.cache_key(namespace, key)
        return self.redis.get(cache_key, default)
    
    def delete_cache(self, namespace: str, key: str) -> bool:
        """
        Delete cache value
        """
        cache_key = self.cache_key(namespace, key)
        return bool(self.redis.delete(cache_key))
    
    def clear_namespace(self, namespace: str) -> int:
        """
        Clear all cache entries in a namespace
        """
        # This would require pattern matching and deletion
        # Implementation would depend on Redis SCAN command
        return 0