"""
Rate limiting to prevent abuse and ensure fair resource usage
"""
import time
from collections import defaultdict, deque
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = Lock()
    
    def is_allowed(self, identifier):
        """Check if request is allowed for given identifier (IP, user_id, etc.)"""
        with self.lock:
            current_time = time.time()
            request_times = self.requests[identifier]
            
            # Remove old requests outside the window
            while request_times and request_times[0] < current_time - self.window_seconds:
                request_times.popleft()
            
            # Check if under limit
            if len(request_times) < self.max_requests:
                request_times.append(current_time)
                return True
            
            return False
    
    def get_remaining(self, identifier):
        """Get remaining requests for identifier"""
        with self.lock:
            current_time = time.time()
            request_times = self.requests[identifier]
            
            # Remove old requests
            while request_times and request_times[0] < current_time - self.window_seconds:
                request_times.popleft()
            
            return max(0, self.max_requests - len(request_times))

# Rate limiters for different endpoints
general_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 req/min
api_limiter = RateLimiter(max_requests=30, window_seconds=60)      # 30 req/min for APIs
payment_limiter = RateLimiter(max_requests=5, window_seconds=300) # 5 req/5min for payments