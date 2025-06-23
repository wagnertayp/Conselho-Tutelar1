"""
Minimal configuration for maximum Heroku stability
"""

# Ultra-conservative database settings for Heroku
MINIMAL_DB_CONFIG = {
    "pool_recycle": 30,
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 5,
    "pool_timeout": 3,
    "echo": False,
    "connect_args": {
        "connect_timeout": 2,
        "application_name": "prosegur_minimal"
    }
}

# Minimal memory management intervals
CLEANUP_INTERVALS = {
    "session_cleanup": 25,      # Clean sessions every 25 requests
    "memory_cleanup": 15,       # Garbage collect every 15 requests
    "analytics_cleanup": 10,    # Clean analytics every 10 requests
    "database_cleanup": 1000    # Database cleanup every 1000 requests
}

# Minimal cache sizes
CACHE_LIMITS = {
    "max_active_users": 20,
    "max_session_age": 120,     # 2 minutes
    "max_cache_size": 50
}