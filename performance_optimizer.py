"""
Performance optimization for high traffic handling
"""
import time
import threading
from functools import wraps
from collections import defaultdict
import gc

class PerformanceOptimizer:
    def __init__(self):
        self.request_times = defaultdict(list)
        self.slow_requests = []
        self.lock = threading.Lock()
        
    def track_request_time(self, route, duration):
        """Track request processing time"""
        with self.lock:
            # Keep only recent times (last 100 per route)
            if len(self.request_times[route]) > 100:
                self.request_times[route] = self.request_times[route][-50:]
            
            self.request_times[route].append(duration)
            
            # Track slow requests (over 2 seconds)
            if duration > 2.0:
                self.slow_requests.append({
                    'route': route,
                    'duration': duration,
                    'timestamp': time.time()
                })
                
                # Keep only recent slow requests
                if len(self.slow_requests) > 50:
                    self.slow_requests = self.slow_requests[-25:]
    
    def get_performance_stats(self):
        """Get performance statistics"""
        with self.lock:
            stats = {}
            for route, times in self.request_times.items():
                if times:
                    avg_time = sum(times) / len(times)
                    max_time = max(times)
                    stats[route] = {
                        'avg_response_time': round(avg_time, 3),
                        'max_response_time': round(max_time, 3),
                        'request_count': len(times)
                    }
            
            return {
                'route_stats': stats,
                'slow_requests_count': len(self.slow_requests),
                'recent_slow_requests': self.slow_requests[-5:]
            }
    
    def force_garbage_collection(self):
        """Force garbage collection to free memory"""
        try:
            collected = gc.collect()
            return collected
        except Exception:
            return 0

def performance_monitor(f):
    """Decorator to monitor route performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            route = getattr(f, '__name__', 'unknown')
            performance_optimizer.track_request_time(route, duration)
            
            # Track in stability monitor and concurrency optimizer
            try:
                from stability_monitor import stability_monitor
                from high_concurrency_optimizer import concurrency_optimizer
                stability_monitor.track_response(duration)
                concurrency_optimizer.track_request_end(duration)
            except:
                pass
    return decorated_function

# Global performance optimizer
performance_optimizer = PerformanceOptimizer()