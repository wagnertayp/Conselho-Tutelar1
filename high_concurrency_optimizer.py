"""
High concurrency optimizer for handling thousands of simultaneous users
"""
import threading
import time
from collections import deque

class HighConcurrencyOptimizer:
    def __init__(self):
        self.request_queue = deque(maxlen=10000)
        self.response_times = deque(maxlen=1000)
        self.concurrent_users = 0
        self.peak_concurrent = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def track_request_start(self):
        """Track when a request starts"""
        with self.lock:
            self.concurrent_users += 1
            if self.concurrent_users > self.peak_concurrent:
                self.peak_concurrent = self.concurrent_users
            
            timestamp = time.time()
            self.request_queue.append(timestamp)
    
    def track_request_end(self, duration):
        """Track when a request ends"""
        with self.lock:
            self.concurrent_users = max(0, self.concurrent_users - 1)
            self.response_times.append(duration)
    
    def get_stats(self):
        """Get concurrency statistics"""
        with self.lock:
            current_time = time.time()
            
            # Calculate requests per minute
            recent_requests = [t for t in self.request_queue if current_time - t < 60]
            requests_per_minute = len(recent_requests)
            
            # Calculate average response time
            avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            
            return {
                'concurrent_users': self.concurrent_users,
                'peak_concurrent': self.peak_concurrent,
                'requests_per_minute': requests_per_minute,
                'avg_response_time': round(avg_response, 3),
                'uptime_hours': round((current_time - self.start_time) / 3600, 2)
            }
    
    def should_throttle(self):
        """Check if we should throttle requests"""
        with self.lock:
            # Throttle if too many concurrent users or slow responses
            return (self.concurrent_users > 2000 or 
                    (self.response_times and sum(self.response_times[-10:]) / min(10, len(self.response_times)) > 2.0))

# Global optimizer instance
concurrency_optimizer = HighConcurrencyOptimizer()