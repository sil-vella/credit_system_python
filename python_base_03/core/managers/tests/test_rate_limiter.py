import unittest
from unittest.mock import patch, MagicMock
from core.managers.rate_limiter_manager import RateLimiterManager
from utils.config.config import Config
import time

class TestRateLimiterManager(unittest.TestCase):
    def setUp(self):
        self.rate_limiter = RateLimiterManager()
        self.test_ip = "127.0.0.1"
        self.test_user = "test_user"
        self.test_api_key = "test_api_key"

    def test_singleton_pattern(self):
        """Test that RateLimiterManager is a singleton."""
        rate_limiter2 = RateLimiterManager()
        self.assertIs(self.rate_limiter, rate_limiter2)

    @patch('core.managers.redis_manager.RedisManager')
    def test_check_rate_limit_first_request(self, mock_redis):
        """Test rate limit check for first request."""
        mock_redis.get.return_value = None
        result = self.rate_limiter.check_rate_limit('ip', self.test_ip)
        self.assertTrue(result['allowed'])
        self.assertEqual(result['remaining'], Config.RATE_LIMIT_IP_REQUESTS - 1)

    @patch('core.managers.redis_manager.RedisManager')
    def test_check_rate_limit_exceeded(self, mock_redis):
        """Test rate limit check when limit is exceeded."""
        mock_redis.get.return_value = str(Config.RATE_LIMIT_IP_REQUESTS)
        mock_redis.ttl.return_value = 60
        result = self.rate_limiter.check_rate_limit('ip', self.test_ip)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['remaining'], 0)

    @patch('core.managers.redis_manager.RedisManager')
    def test_check_rate_limit_redis_error(self, mock_redis):
        """Test rate limit check when Redis error occurs."""
        mock_redis.get.side_effect = Exception("Redis error")
        result = self.rate_limiter.check_rate_limit('ip', self.test_ip)
        self.assertTrue(result['allowed'])  # Should allow request on error
        self.assertEqual(result['remaining'], -1)

    def test_reset_rate_limit(self):
        """Test resetting rate limit."""
        with patch('core.managers.redis_manager.RedisManager.delete') as mock_delete:
            mock_delete.return_value = True
            result = self.rate_limiter.reset_rate_limit('ip', self.test_ip)
            self.assertTrue(result)

    @patch('core.managers.redis_manager.RedisManager')
    def test_rate_limit_window(self, mock_redis):
        """Test rate limit window expiration."""
        # First request
        mock_redis.get.return_value = None
        result1 = self.rate_limiter.check_rate_limit('ip', self.test_ip)
        
        # Second request after window expires
        mock_redis.get.return_value = None
        result2 = self.rate_limiter.check_rate_limit('ip', self.test_ip)
        
        self.assertTrue(result1['allowed'])
        self.assertTrue(result2['allowed'])
        self.assertEqual(result2['remaining'], Config.RATE_LIMIT_IP_REQUESTS - 1)

if __name__ == '__main__':
    unittest.main() 