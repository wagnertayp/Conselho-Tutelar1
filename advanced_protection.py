"""
Advanced anti-cloning protection system
Implements multiple sophisticated techniques to prevent unauthorized access
"""
import hashlib
import hmac
import time
import random
import base64
from flask import request, Response, session
from functools import wraps

class AdvancedProtection:
    def __init__(self, secret_key="prosegur_protection_2025"):
        self.secret_key = secret_key.encode()
        self.blocked_ips = set()
        self.suspicious_patterns = {}
        
    def generate_session_token(self, user_agent, ip):
        """Generate unique session token based on device fingerprint"""
        timestamp = str(int(time.time() // 300))  # 5-minute windows
        fingerprint = f"{user_agent}{ip}{timestamp}"
        return hmac.new(self.secret_key, fingerprint.encode(), hashlib.sha256).hexdigest()
    
    def validate_session_token(self, token, user_agent, ip):
        """Validate session token to ensure consistency"""
        for window in range(3):  # Check current and 2 previous windows
            timestamp = str(int(time.time() // 300) - window)
            fingerprint = f"{user_agent}{ip}{timestamp}"
            expected = hmac.new(self.secret_key, fingerprint.encode(), hashlib.sha256).hexdigest()
            if hmac.compare_digest(token, expected):
                return True
        return False
    
    def analyze_request_patterns(self, ip, user_agent):
        """Analyze request patterns for bot behavior"""
        current_time = time.time()
        
        if ip not in self.suspicious_patterns:
            self.suspicious_patterns[ip] = {
                'requests': [],
                'user_agents': set(),
                'first_seen': current_time
            }
        
        pattern = self.suspicious_patterns[ip]
        pattern['requests'].append(current_time)
        pattern['user_agents'].add(user_agent)
        
        # Clean old requests (older than 10 minutes)
        pattern['requests'] = [t for t in pattern['requests'] if current_time - t < 600]
        
        # Detect suspicious patterns
        suspicious_score = 0
        
        # Too many requests in short time
        if len(pattern['requests']) > 50:
            suspicious_score += 5
        
        # Multiple user agents from same IP
        if len(pattern['user_agents']) > 3:
            suspicious_score += 3
        
        # Regular timing intervals (bot pattern)
        if len(pattern['requests']) >= 5:
            intervals = [pattern['requests'][i] - pattern['requests'][i-1] 
                        for i in range(1, len(pattern['requests']))]
            avg_interval = sum(intervals) / len(intervals)
            if 0.5 < avg_interval < 2.0:  # Too regular
                suspicious_score += 4
        
        return suspicious_score >= 5
    
    def check_javascript_execution(self):
        """Check if JavaScript challenges were completed"""
        js_token = request.headers.get('X-JS-Token')
        if not js_token:
            return False
        
        try:
            # Decode and validate JavaScript challenge response
            decoded = base64.b64decode(js_token).decode()
            parts = decoded.split(':')
            if len(parts) != 3:
                return False
            
            timestamp, challenge, response = parts
            expected = hashlib.sha256(f"{challenge}{self.secret_key.decode()}".encode()).hexdigest()
            
            # Check if response is correct and recent (within 30 seconds)
            if (hmac.compare_digest(response, expected) and 
                time.time() - float(timestamp) < 30):
                return True
        except:
            pass
        
        return False
    
    def analyze_browser_fingerprint(self):
        """Analyze browser fingerprint for authenticity"""
        headers = dict(request.headers)
        
        # Calculate fingerprint consistency score
        consistency_score = 0
        
        # Check for mobile-specific headers
        mobile_headers = [
            'X-Requested-With',
            'X-Mobile',
            'X-WAP-Profile',
            'Accept-CH-Mobile'
        ]
        
        user_agent = headers.get('User-Agent', '').lower()
        is_mobile_ua = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone'])
        
        if is_mobile_ua:
            consistency_score += 2
        
        # Check Accept headers consistency
        accept_header = headers.get('Accept', '')
        if 'text/html' in accept_header and 'application/xhtml+xml' in accept_header:
            consistency_score += 1
        
        # Check for presence of standard browser headers
        required_headers = ['Accept', 'Accept-Language', 'Accept-Encoding']
        present_headers = sum(1 for h in required_headers if h in headers)
        consistency_score += present_headers
        
        # Check for suspicious automation headers
        automation_headers = ['webdriver', 'selenium', 'phantomjs', 'headless']
        for header_name, header_value in headers.items():
            if any(auto in header_value.lower() for auto in automation_headers):
                consistency_score -= 5
        
        return consistency_score >= 3
    
    def generate_challenge_response(self):
        """Generate JavaScript challenge for client verification"""
        challenge = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
        timestamp = str(time.time())
        
        js_code = f"""
        <script>
        (function() {{
            function computeResponse(challenge, secret) {{
                var crypto = window.crypto || window.msCrypto;
                if (!crypto || !crypto.subtle) return null;
                
                var encoder = new TextEncoder();
                var data = encoder.encode(challenge + secret);
                
                return crypto.subtle.digest('SHA-256', data).then(function(hash) {{
                    var hashArray = Array.from(new Uint8Array(hash));
                    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
                }});
            }}
            
            var challenge = '{challenge}';
            var secret = '{hashlib.sha256(self.secret_key).hexdigest()[:16]}';
            var timestamp = '{timestamp}';
            
            computeResponse(challenge, secret).then(function(response) {{
                var token = btoa(timestamp + ':' + challenge + ':' + response);
                
                // Add token to all future requests
                var originalFetch = window.fetch;
                window.fetch = function() {{
                    var args = Array.prototype.slice.call(arguments);
                    if (args[1]) {{
                        args[1].headers = args[1].headers || {{}};
                        args[1].headers['X-JS-Token'] = token;
                    }} else {{
                        args[1] = {{ headers: {{ 'X-JS-Token': token }} }};
                    }}
                    return originalFetch.apply(this, args);
                }};
                
                // Add to XMLHttpRequest
                var originalOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function() {{
                    originalOpen.apply(this, arguments);
                    this.setRequestHeader('X-JS-Token', token);
                }};
            }}).catch(function() {{
                window.location.href = 'about:blank';
            }});
            
            // Additional anti-tampering checks
            setInterval(function() {{
                if (window.navigator.webdriver || 
                    window.chrome && window.chrome.runtime && window.chrome.runtime.onConnect ||
                    window.callPhantom || window._phantom || window.phantom) {{
                    window.location.href = 'about:blank';
                }}
            }}, 1000);
        }})();
        </script>
        """
        return js_code

protection = AdvancedProtection()

def ultra_secure_mobile_only(f):
    """
    Ultra-secure mobile-only decorator with multiple protection layers
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Layer 1: Check if IP is blocked
        if ip in protection.blocked_ips:
            return Response('', status=404)
        
        # Layer 2: Analyze request patterns for bot behavior
        if protection.analyze_request_patterns(ip, user_agent):
            protection.blocked_ips.add(ip)
            return Response('', status=404)
        
        # Layer 3: Browser fingerprint analysis
        if not protection.analyze_browser_fingerprint():
            return Response('', status=404)
        
        # Layer 4: Session token validation
        session_token = session.get('protection_token')
        if session_token:
            if not protection.validate_session_token(session_token, user_agent, ip):
                return Response('', status=404)
        else:
            # Generate new session token
            session['protection_token'] = protection.generate_session_token(user_agent, ip)
        
        # Layer 5: JavaScript execution check (after first request)
        if 'protection_js_verified' in session:
            if not protection.check_javascript_execution():
                # Return challenge page
                challenge_js = protection.generate_challenge_response()
                return Response(f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Verificação</title>
                    <style>
                        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                        .loading {{ text-align: center; margin-top: 50px; }}
                    </style>
                </head>
                <body>
                    <div class="loading">
                        <h3>Verificando dispositivo...</h3>
                        <p>Aguarde um momento.</p>
                    </div>
                    {challenge_js}
                    <script>
                        setTimeout(function() {{
                            window.location.reload();
                        }}, 3000);
                    </script>
                </body>
                </html>
                ''', mimetype='text/html')
        else:
            session['protection_js_verified'] = True
        
        # Layer 6: Mobile device validation
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'touch']
        if not any(indicator in user_agent.lower() for indicator in mobile_indicators):
            return Response('', status=404)
        
        # All checks passed - allow access
        return f(*args, **kwargs)
    
    return decorated_function