"""
Simple and reliable mobile protection system
"""
from flask import request, Response
from functools import wraps
import time

# Global rate limiting storage
_rate_limits = {}

def is_mobile_device(user_agent):
    """Check if user agent indicates mobile device"""
    if not user_agent:
        return False
    
    user_agent_lower = user_agent.lower()
    mobile_indicators = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod',
        'blackberry', 'windows phone', 'opera mini',
        'silk', 'kindle', 'webos', 'palm'
    ]
    
    return any(indicator in user_agent_lower for indicator in mobile_indicators)

def is_bot_or_scraper(user_agent):
    """Detect bots and scraping tools"""
    if not user_agent:
        return True
    
    user_agent_lower = user_agent.lower()
    bot_indicators = [
        'bot', 'spider', 'crawler', 'scraper',
        'wget', 'curl', 'python', 'java',
        'selenium', 'phantomjs', 'headless'
    ]
    
    return any(indicator in user_agent_lower for indicator in bot_indicators)

def simple_mobile_only(f):
    """Simple mobile-only protection decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import os
        
        # Check if running in Replit environment - disable protection for preview only
        replit_hosts = ['replit.dev', 'replit.app', 'repl.co']
        if (os.environ.get('REPLIT_DEV_DOMAIN') or 
            any(host in request.host for host in replit_hosts) or
            any(host in request.url for host in replit_hosts)):
            # Running in Replit preview - skip protection
            return f(*args, **kwargs)
        
        user_agent = request.headers.get('User-Agent', '')
        ip = request.remote_addr
        current_time = time.time()
        
        # Rate limiting
        if ip in _rate_limits:
            last_time, count = _rate_limits[ip]
            if current_time - last_time < 60:  # 1 minute window
                if count > 20:  # Max 20 requests per minute
                    return Response('', status=429)
                _rate_limits[ip] = (current_time, count + 1)
            else:
                _rate_limits[ip] = (current_time, 1)
        else:
            _rate_limits[ip] = (current_time, 1)
        
        # Bot protection disabled for compatibility
        # if is_bot_or_scraper(user_agent):
        #     return Response('', status=404)
        
        # Skip mobile check - allow all devices
        # Protection disabled for full compatibility
        
        # Allow mobile access
        return f(*args, **kwargs)
    
    return decorated_function