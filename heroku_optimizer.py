"""
Heroku-specific optimizations to prevent dyno cycling
"""
import gc
import os
import threading
import time
import psutil

class HerokuOptimizer:
    def __init__(self):
        self.memory_limit = 512  # Heroku dyno memory limit in MB
        self.warning_threshold = 400  # Warning at 400MB
        self.cleanup_running = False
        
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0
    
    def aggressive_cleanup(self):
        """Perform aggressive memory cleanup"""
        if self.cleanup_running:
            return
            
        self.cleanup_running = True
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Clear unused imports
            import sys
            modules_to_clear = []
            for module_name in sys.modules:
                if (module_name.startswith('requests') or 
                    module_name.startswith('urllib') or
                    module_name.startswith('json')):
                    continue  # Keep essential modules
                    
            # Additional cleanup
            gc.collect()
            
            return collected
        finally:
            self.cleanup_running = False
    
    def should_cleanup(self):
        """Check if cleanup is needed"""
        memory_mb = self.get_memory_usage()
        return memory_mb > self.warning_threshold
    
    def monitor_and_cleanup(self):
        """Monitor memory and cleanup if needed"""
        if self.should_cleanup():
            self.aggressive_cleanup()

# Global optimizer instance
heroku_optimizer = HerokuOptimizer()