from core.managers.redis_manager import RedisManager
from tools.logger.custom_logging import custom_log
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, Any
from flask import request
from utils.config.config import Config

class RateLimiterManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimiterManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not RateLimiterManager._initialized:
            self.redis_manager = RedisManager()
            self._setup_config()
            RateLimiterManager._initialized = True
            custom_log("RateLimiterManager initialized")

    def _setup_config(self):
        """Set up rate limiting configuration from Config."""
        self.config = {
            'ip': {
                'requests': Config.RATE_LIMIT_IP_REQUESTS,
                'window': Config.RATE_LIMIT_IP_WINDOW,
                'prefix': Config.RATE_LIMIT_IP_PREFIX
            },
            'user': {
                'requests': Config.RATE_LIMIT_USER_REQUESTS,
                'window': Config.RATE_LIMIT_USER_WINDOW,
                'prefix': Config.RATE_LIMIT_USER_PREFIX
            },
            'api_key': {
                'requests': Config.RATE_LIMIT_API_KEY_REQUESTS,
                'window': Config.RATE_LIMIT_API_KEY_WINDOW,
                'prefix': Config.RATE_LIMIT_API_KEY_PREFIX
            }
        }

    def _get_client_ip(self) -> str:
        """Get the client's IP address from the request."""
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            # If behind a proxy
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
        return request.environ.get('REMOTE_ADDR', 'unknown')

    def _generate_redis_key(self, identifier: str, limit_type: str) -> str:
        """Generate a Redis key for rate limiting."""
        prefix = self.config[limit_type]['prefix']
        return f"{prefix}:{identifier}"

    def check_rate_limit(self, limit_type: str = 'ip', identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if the request is within rate limits.
        
        Args:
            limit_type: Type of rate limit ('ip', 'user', 'api_key')
            identifier: Optional identifier (if not provided, will use IP)
            
        Returns:
            Dict containing:
                - allowed: bool
                - remaining: int
                - reset_time: int
        """
        if not Config.RATE_LIMIT_ENABLED:
            return {
                'allowed': True,
                'remaining': -1,
                'reset_time': 0
            }

        if limit_type not in self.config:
            return {
                'allowed': True,
                'remaining': -1,
                'reset_time': 0
            }

        # Get identifier (default to IP if not provided)
        if not identifier and limit_type == 'ip':
            identifier = self._get_client_ip()

        if not identifier:
            return {
                'allowed': True,
                'remaining': -1,
                'reset_time': 0
            }

        # Generate Redis key
        key = self._generate_redis_key(identifier, limit_type)
        limit_config = self.config[limit_type]

        # Get current count
        current = self.redis_manager.get(key)
        if current is None:
            # First request in window
            self.redis_manager.set(key, 1, expire=limit_config['window'])
            return {
                'allowed': True,
                'remaining': limit_config['requests'] - 1,
                'reset_time': int(time.time()) + limit_config['window']
            }

        current = int(current)
        if current >= limit_config['requests']:
            # Rate limit exceeded
            ttl = self.redis_manager.ttl(key)
            return {
                'allowed': False,
                'remaining': 0,
                'reset_time': int(time.time()) + ttl
            }

        # Increment counter
        self.redis_manager.incr(key)
        return {
            'allowed': True,
            'remaining': limit_config['requests'] - (current + 1),
            'reset_time': int(time.time()) + self.redis_manager.ttl(key)
        }

    def reset_rate_limit(self, limit_type: str, identifier: str) -> bool:
        """Reset the rate limit for a given identifier."""
        key = self._generate_redis_key(identifier, limit_type)
        return self.redis_manager.delete(key) 