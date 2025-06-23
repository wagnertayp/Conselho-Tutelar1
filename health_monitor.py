"""
Health monitoring system to track application performance and identify crash causes
"""
import os
import time
import logging
from datetime import datetime
from threading import Thread
import json

class HealthMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_errors = []
        self.memory_peaks = []
        self.running = True
        
    def log_request(self):
        """Log incoming request"""
        self.request_count += 1
        
    def log_error(self, error_msg, endpoint=None):
        """Log error with timestamp"""
        self.error_count += 1
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error_msg),
            'endpoint': endpoint,
            'memory_mb': self.get_memory_usage()
        }
        self.last_errors.append(error_entry)
        
        # Keep only last 10 errors
        if len(self.last_errors) > 10:
            self.last_errors.pop(0)
            
        logging.error(f"Health Monitor - Error: {error_msg} at {endpoint}")
        
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return round(usage.ru_maxrss / 1024, 2)  # Convert to MB
        except:
            return 0
            
    def get_system_stats(self):
        """Get system resource usage"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                'process_memory_mb': round(usage.ru_maxrss / 1024, 2),
                'user_time': usage.ru_utime,
                'system_time': usage.ru_stime
            }
        except:
            return {}
            
    def monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                current_memory = self.get_memory_usage()
                
                # Track memory peaks  
                if current_memory > 100:  # Alert if process uses >100MB
                    self.memory_peaks.append({
                        'timestamp': datetime.now().isoformat(),
                        'memory_mb': current_memory,
                        'requests': self.request_count,
                        'errors': self.error_count
                    })
                    
                    # Keep only last 5 peaks
                    if len(self.memory_peaks) > 5:
                        self.memory_peaks.pop(0)
                        
                time.sleep(30)  # Check every 30 seconds
            except:
                pass
                
    def start_monitoring(self):
        """Start background monitoring thread"""
        monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        
    def get_health_report(self):
        """Get comprehensive health report"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': round(uptime, 2),
            'uptime_minutes': round(uptime / 60, 2),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': round(self.error_count / max(self.request_count, 1) * 100, 2),
            'current_memory_mb': self.get_memory_usage(),
            'system_stats': self.get_system_stats(),
            'recent_errors': self.last_errors[-3:],  # Last 3 errors
            'memory_peaks': self.memory_peaks[-3:],   # Last 3 memory peaks
            'status': 'healthy' if self.error_count < 10 else 'degraded'
        }

# Global monitor instance
health_monitor = HealthMonitor()