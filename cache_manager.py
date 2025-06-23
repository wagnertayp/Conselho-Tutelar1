"""
Simple in-memory cache to reduce database load and API calls
"""
import time
from threading import Lock
from collections import OrderedDict

class SimpleCache:
    def __init__(self, max_size=50000, default_ttl=600):
        self.cache = OrderedDict()
        self.timestamps = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def get(self, key):
        """Get value from cache if not expired"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check if expired
            if time.time() - self.timestamps[key] > self.default_ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # Move to end (recently accessed)
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def set(self, key, value, ttl=None):
        """Set value in cache"""
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl
            
            # Remove oldest items if cache is full
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self):
        """Get current cache size"""
        return len(self.cache)

# Global cache instances - optimized for 3000+ users
page_cache = SimpleCache(max_size=5000, default_ttl=60)  # 1 minute TTL
api_cache = SimpleCache(max_size=20000, default_ttl=300)  # 5 minute TTL