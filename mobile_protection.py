"""
Server-side mobile protection to prevent desktop cloning
"""
from flask import request, abort, Response
from functools import wraps
import re
import time

def is_mobile_device(user_agent):
    """
    Detect if the request is coming from a mobile device
    """
    if not user_agent:
        return False
    
    user_agent = user_agent.lower()
    
    # Mobile device indicators
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 
        'blackberry', 'windows phone', 'opera mini', 
        'silk', 'kindle', 'webos', 'palm'
    ]
    
    # Check for mobile keywords
    for keyword in mobile_keywords:
        if keyword in user_agent:
            return True
    
    return False

def is_scraping_tool(user_agent):
    """
    Detect common scraping tools and bots
    """
    if not user_agent:
        return True  # No user agent is suspicious
    
    user_agent = user_agent.lower()
    
    scraping_tools = [
        'wget', 'curl', 'httrack', 'webzip', 'teleport',
        'offline explorer', 'web copier', 'sitesuck',
        'python', 'java', 'go-http-client', 'node',
        'bot', 'spider', 'crawler', 'scraper'
    ]
    
    for tool in scraping_tools:
        if tool in user_agent:
            return True
    
    return False

def is_desktop_browser(user_agent):
    """
    Detect desktop browsers without mobile indicators
    """
    if not user_agent:
        return True
    
    user_agent = user_agent.lower()
    
    # Desktop browser patterns
    desktop_patterns = [
        r'windows nt.*chrome',
        r'macintosh.*chrome',
        r'x11.*linux.*chrome',
        r'windows nt.*firefox',
        r'macintosh.*firefox',
        r'windows nt.*edge',
        r'macintosh.*safari(?!.*mobile)',
    ]
    
    # Mobile exclusions
    mobile_exclusions = [
        'mobile', 'android', 'iphone', 'ipad'
    ]
    
    # Check if it matches desktop patterns and lacks mobile indicators
    has_desktop_pattern = any(re.search(pattern, user_agent) for pattern in desktop_patterns)
    has_mobile_indicator = any(mobile in user_agent for mobile in mobile_exclusions)
    
    return has_desktop_pattern and not has_mobile_indicator

def mobile_only(f):
    """
    Decorator to protect routes from desktop access with advanced detection
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_agent = request.headers.get('User-Agent', '')
        
        # Advanced fingerprinting checks
        fingerprint_score = 0
        
        # Check 1: User-Agent analysis
        if is_scraping_tool(user_agent):
            return Response('', status=204)
        
        # Check 2: Missing mobile-specific headers
        accept_header = request.headers.get('Accept', '')
        if 'text/html' in accept_header and 'mobile' not in user_agent.lower():
            fingerprint_score += 2
        
        # Check 3: Screen resolution hints (from viewport)
        viewport_width = request.headers.get('Viewport-Width', '')
        if viewport_width and int(viewport_width) > 1200:
            fingerprint_score += 1
        
        # Check 4: Connection type analysis
        connection = request.headers.get('Connection', '')
        if 'keep-alive' in connection.lower() and 'mobile' not in user_agent.lower():
            fingerprint_score += 1
        
        # Check 5: Suspicious header combinations
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip, deflate' in accept_encoding and not is_mobile_device(user_agent):
            fingerprint_score += 1
        
        # Check 6: Missing touch capability indicators
        if 'touch' not in user_agent.lower() and 'mobile' not in user_agent.lower():
            fingerprint_score += 1
        
        # Check 7: Desktop browser patterns
        if is_desktop_browser(user_agent) and not is_mobile_device(user_agent):
            fingerprint_score += 3
        
        # Block if fingerprint score indicates desktop/bot
        if fingerprint_score >= 3:
            # Generate different responses to confuse scrapers
            import random
            responses = [
                Response('', status=404),
                Response('', status=503),
                Response('Access denied', status=403),
                Response('', status=204),
                Response('''
                <!DOCTYPE html>
                <html><head><title></title></head>
                <body><script>window.location.href='about:blank';</script></body>
                </html>
                ''', mimetype='text/html')
            ]
            return random.choice(responses)
        
        # Additional check: Rate limiting per IP for suspicious patterns
        ip = request.remote_addr
        current_time = time.time()
        
        # Simple rate limiting in memory
        if not hasattr(decorated_function, '_ip_requests'):
            decorated_function._ip_requests = {}
        
        if ip in decorated_function._ip_requests:
            last_request, count = decorated_function._ip_requests[ip]
            if current_time - last_request < 60:  # Within 1 minute
                if count > 10:  # More than 10 requests per minute
                    return Response('Rate limited', status=429)
                decorated_function._ip_requests[ip] = (current_time, count + 1)
            else:
                decorated_function._ip_requests[ip] = (current_time, 1)
        else:
            decorated_function._ip_requests[ip] = (current_time, 1)
        
        # Allow mobile devices to proceed
        return f(*args, **kwargs)
    
    return decorated_function

def check_mobile_access():
    """
    Check if current request should be allowed based on mobile detection
    """
    user_agent = request.headers.get('User-Agent', '')
    
    # Block scraping tools
    if is_scraping_tool(user_agent):
        return False
    
    # Block desktop browsers
    if is_desktop_browser(user_agent) and not is_mobile_device(user_agent):
        return False
    
    return True