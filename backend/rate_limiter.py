from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, HTTPException
import redis
import json
import hashlib
from functools import wraps
import time

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

class AdvancedRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost', port=6379, decode_responses=True
        )
        self.rate_limits = {
            'login': {'limit': 5, 'window': 300},  # 5 attempts per 5 minutes
            'predict': {'limit': 10, 'window': 60},  # 10 predictions per minute
            'upload': {'limit': 20, 'window': 3600},  # 20 uploads per hour
            'api_call': {'limit': 100, 'window': 60}  # 100 API calls per minute
        }
    
    def check_rate_limit(self, key: str, limit_type: str = 'api_call'):
        """Check if request is within rate limit"""
        config = self.rate_limits.get(limit_type, self.rate_limits['api_call'])
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        # Clean old entries
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_count = self.redis_client.zcard(key)
        
        if current_count >= config['limit']:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Max {config['limit']} requests per {config['window']} seconds"
            )
        
        # Add current request
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, config['window'])
        
        return True

rate_limiter = AdvancedRateLimiter()