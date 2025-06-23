"""
Heroku stability monitor to prevent dyno cycling
"""
import gc
import time
import threading
from collections import deque

class StabilityMonitor:
    def __init__(self):
        self.response_times = deque(maxlen=100)
        self.error_count = 0
        self.last_cleanup = time.time()
        self.cleanup_interval = 30  # seconds
        self.lock = threading.Lock()
        
    def track_response(self, duration):
        """Track response time"""
        with self.lock:
            self.response_times.append(duration)
            
            # Check if we need emergency cleanup
            if duration > 1.0:  # Response over 1 second
                self.emergency_cleanup()
    
    def emergency_cleanup(self):
        """Emergency memory cleanup for slow responses"""
        current_time = time.time()
        if current_time - self.last_cleanup > 10:  # Don't cleanup too frequently
            gc.collect()
            self.last_cleanup = current_time
    
    def get_avg_response_time(self):
        """Get average response time"""
        with self.lock:
            if not self.response_times:
                return 0
            return sum(self.response_times) / len(self.response_times)
    
    def is_under_stress(self):
        """Check if system is under stress"""
        avg_time = self.get_avg_response_time()
        return avg_time > 0.8  # Over 800ms average

# Global stability monitor
stability_monitor = StabilityMonitor()