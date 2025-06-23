"""
Real-time analytics system for tracking user activity and sales
"""
import os
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
import logging

class AnalyticsTracker:
    def __init__(self):
        self.active_users = set()
        self.page_views = defaultdict(int)
        self.page_views_by_route = defaultdict(int)
        self.sales_today = []
        self.user_sessions = {}
        self.lock = Lock()
        
        # Session timeout (5 minutes)
        self.session_timeout = 1800  # 30 minutes for enterprise scale
        
    def track_user_visit(self, user_id, route='/'):
        """Track a user visit to a specific route"""
        # Skip tracking for static files and health checks to reduce load
        if (route.startswith('/static/') or route == '/health' or 
            route == '/favicon.ico' or route.startswith('/api/')):
            return
            
        with self.lock:
            current_time = time.time()
            
            # Optimized for 3000+ concurrent users
            if len(self.active_users) > 5000:
                # Remove oldest 1000 users when we hit 5000 to maintain performance
                old_sessions = sorted(self.user_sessions.items(), key=lambda x: x[1])[:1000]
                for old_user, _ in old_sessions:
                    self.active_users.discard(old_user)
                    self.user_sessions.pop(old_user, None)
            
            # Add user to active users
            self.active_users.add(user_id)
            
            # Update user session
            self.user_sessions[user_id] = current_time
            
            # Track page view (limit growth)
            today = datetime.now().strftime('%Y-%m-%d')
            self.page_views[today] += 1
            self.page_views_by_route[route] += 1
            
            # Clean up old sessions much less frequently for high traffic
            if len(self.user_sessions) % 500 == 0:  # Only cleanup every 500 requests
                self._cleanup_sessions()
            
    def track_sale(self, customer_name, amount, customer_id=None):
        """Track a new sale"""
        with self.lock:
            sale_data = {
                'customerName': customer_name,
                'amount': float(amount),
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'customerId': customer_id,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            self.sales_today.append(sale_data)
            
            # Increased capacity for high volume sales
            if len(self.sales_today) > 10000:
                self.sales_today = self.sales_today[-5000:]  # Keep last 5000 sales
            
            logging.info(f"New sale tracked: {customer_name} - R$ {amount}")
            
    def _cleanup_sessions(self):
        """Remove inactive user sessions"""
        current_time = time.time()
        inactive_users = []
        
        for user_id, last_seen in self.user_sessions.items():
            if current_time - last_seen > self.session_timeout:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            self.active_users.discard(user_id)
            self.user_sessions.pop(user_id, None)
        
        # Also clean up old page view data (keep only today and yesterday)
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        dates_to_keep = {today, yesterday}
        dates_to_remove = [date for date in self.page_views.keys() if date not in dates_to_keep]
        
        for date in dates_to_remove:
            self.page_views.pop(date, None)
    
    def get_analytics_data(self):
        """Get current analytics data"""
        with self.lock:
            self._cleanup_sessions()
            
            today = datetime.now().strftime('%Y-%m-%d')
            today_sales = [sale for sale in self.sales_today if sale['date'] == today]
            
            total_revenue = sum(sale['amount'] for sale in today_sales)
            
            return {
                'activeUsers': len(self.active_users),
                'pageViews': self.page_views.get(today, 0),
                'totalSales': len(today_sales),
                'totalRevenue': total_revenue,
                'pageViewsByRoute': dict(self.page_views_by_route),
                'recentSales': today_sales[-10:] if today_sales else []  # Last 10 sales
            }
    
    def simulate_activity(self):
        """Simulate some user activity for demo purposes"""
        import random
        
        # Reduced simulation to prevent memory issues
        for i in range(random.randint(5, 15)):
            user_id = f"user_{random.randint(1000, 9999)}"
            route = random.choice(['/', '/vagas', '/agendamento', '/pagamento'])
            self.track_user_visit(user_id, route)
        
        # Simulate occasional sales only
        if random.random() < 0.3:  # 30% chance of a sale
            sample_names = [
                "João Silva", "Maria Santos", "Carlos Oliveira", "Ana Costa",
                "Pedro Almeida", "Lucia Ferreira", "Roberto Lima", "Patricia Souza"
            ]
            
            name = random.choice(sample_names)
            amount = 73.40  # Fixed amount for training ammunition
            self.track_sale(name, amount)

# Global analytics tracker instance
analytics_tracker = AnalyticsTracker()