"""
Simple Rate Limiting for Biped Platform
Provides basic protection against abuse without external dependencies
"""

import time
import hashlib
import logging
from typing import Dict, Tuple, Optional
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

class SimpleRateLimiter:
    """In-memory rate limiter for basic protection"""
    
    def __init__(self):
        # Store: {client_id: {'count': int, 'reset_time': float, 'blocked_until': float}}
        self.clients: Dict[str, Dict[str, float]] = {}
        self.rules = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'auth': {'requests': 5, 'window': 900},         # 5 auth attempts per 15 minutes
            'api': {'requests': 200, 'window': 3600},       # 200 API calls per hour
            'search': {'requests': 50, 'window': 300},      # 50 searches per 5 minutes
            'job_posting': {'requests': 10, 'window': 3600} # 10 job posts per hour
        }
        
        # Progressive blocking
        self.block_durations = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
    
    def get_client_id(self, request) -> str:
        """Generate client identifier from request"""
        # Use IP address as primary identifier
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Include user agent for additional uniqueness (hashed for privacy)
        user_agent = request.headers.get('User-Agent', '')
        user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        
        return f"{client_ip}_{user_agent_hash}"
    
    def is_allowed(self, client_id: str, rule_name: str = 'default') -> Tuple[bool, Dict[str, any]]:
        """Check if request is allowed"""
        current_time = time.time()
        rule = self.rules.get(rule_name, self.rules['default'])
        
        # Initialize client if not exists
        if client_id not in self.clients:
            self.clients[client_id] = {
                'count': 0,
                'reset_time': current_time + rule['window'],
                'blocked_until': 0,
                'violations': 0
            }
        
        client_data = self.clients[client_id]
        
        # Check if client is currently blocked
        if current_time < client_data['blocked_until']:
            remaining_time = int(client_data['blocked_until'] - current_time)
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Too many requests. Try again in {remaining_time} seconds.',
                'retry_after': remaining_time
            }
        
        # Reset window if expired
        if current_time > client_data['reset_time']:
            client_data['count'] = 0
            client_data['reset_time'] = current_time + rule['window']
        
        # Check rate limit
        if client_data['count'] >= rule['requests']:
            # Apply progressive blocking
            violations = client_data['violations']
            block_duration = self.block_durations[min(violations, len(self.block_durations) - 1)]
            
            client_data['blocked_until'] = current_time + block_duration
            client_data['violations'] += 1
            
            logger.warning(f"Rate limit exceeded for client {client_id}. "
                          f"Blocked for {block_duration} seconds. "
                          f"Violations: {violations + 1}")
            
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded. Blocked for {block_duration} seconds.',
                'retry_after': block_duration
            }
        
        # Allow request and increment counter
        client_data['count'] += 1
        
        return True, {
            'requests_remaining': rule['requests'] - client_data['count'],
            'reset_time': client_data['reset_time']
        }

# Global rate limiter instance
rate_limiter = SimpleRateLimiter()

def rate_limit(rule_name: str = 'default'):
    """Decorator to apply rate limiting to Flask routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = rate_limiter.get_client_id(request)
            allowed, result = rate_limiter.is_allowed(client_id, rule_name)
            
            if not allowed:
                response = jsonify(result)
                response.status_code = 429  # Too Many Requests
                response.headers['Retry-After'] = str(result.get('retry_after', 60))
                return response
            
            # Store rate limit info for potential use in response headers
            g.rate_limit_info = result
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# For backward compatibility with existing code
limiter = rate_limiter
