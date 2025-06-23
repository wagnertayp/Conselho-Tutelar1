"""
Enterprise-scale optimizations for handling thousands of concurrent users
"""
import threading
import time
from collections import defaultdict

class EnterpriseScaler:
    def __init__(self):
        self.request_stats = defaultdict(int)
        self.last_stats_reset = time.time()
        self.lock = threading.Lock()
        
    def track_request(self, route):
        """Track request for load balancing insights"""
        with self.lock:
            self.request_stats[route] += 1
            
            # Reset stats every 5 minutes
            if time.time() - self.last_stats_reset > 300:
                self.request_stats.clear()
                self.last_stats_reset = time.time()
    
    def get_request_distribution(self):
        """Get current request distribution"""
        with self.lock:
            return dict(self.request_stats)

# Enterprise database configuration for high concurrency
ENTERPRISE_DB_CONFIG = {
    "pool_recycle": 300,        # 5 minutes
    "pool_pre_ping": True,
    "pool_size": 50,            # Increased for high concurrency
    "max_overflow": 100,        # Allow burst capacity
    "pool_timeout": 10,         # Reasonable timeout
    "echo": False,
    "connect_args": {
        "connect_timeout": 5,
        "application_name": "prosegur_enterprise",
        "sslmode": "prefer"
    }
}

# High-capacity memory management
ENTERPRISE_CLEANUP = {
    "session_cleanup_interval": 100,    # Less frequent for performance
    "memory_cleanup_interval": 200,     # Less frequent garbage collection
    "analytics_max_users": 500,         # Higher capacity
    "cache_timeout": 600,               # 10 minute cache
    "max_session_age": 1800             # 30 minutes
}

enterprise_scaler = EnterpriseScaler()