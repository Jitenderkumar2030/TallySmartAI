import redis
import pickle
import hashlib
import json
from functools import wraps
from datetime import datetime, timedelta
import os

class EnhancedCacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.default_expiry = 3600  # 1 hour
        
    def cache_result(self, expiry=None, key_prefix=""):
        """Enhanced caching decorator with better key management"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create unique cache key
                func_name = f"{key_prefix}{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                key_hash = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"{func_name}:{key_hash}"
                
                try:
                    # Try to get from cache
                    cached = self.redis_client.get(cache_key)
                    if cached:
                        return pickle.loads(cached)
                except Exception as e:
                    print(f"Cache read error: {e}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                try:
                    # Cache the result
                    cache_expiry = expiry or self.default_expiry
                    self.redis_client.setex(
                        cache_key, 
                        cache_expiry, 
                        pickle.dumps(result)
                    )
                except Exception as e:
                    print(f"Cache write error: {e}")
                
                return result
            return wrapper
        return decorator
    
    def invalidate_pattern(self, pattern):
        """Invalidate cache by pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                return len(keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")
        return 0
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))
            }
        except:
            return {'status': 'disconnected'}

cache_manager = EnhancedCacheManager()
