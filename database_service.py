"""
Database service for analytics and user tracking
"""
from datetime import datetime, timedelta
from sqlalchemy import func
# Models will be imported from app context
import logging

class DatabaseAnalytics:
    def __init__(self):
        # Import models when class is instantiated
        from app import db
        from models import UserSession, PageView, Sale, AnalyticsData, Registration
        self.db = db
        self.UserSession = UserSession
        self.PageView = PageView
        self.Sale = Sale
        self.AnalyticsData = AnalyticsData
        self.Registration = Registration
    
    def track_user_visit(self, user_id, route, ip_address=None, user_agent=None):
        """Track a user visit to a specific route"""
        try:
            # Skip tracking for static files and health checks
            if route.startswith('/static/') or route == '/health' or route == '/favicon.ico':
                return
            
            # Update or create user session
            session = self.UserSession.query.filter_by(user_id=user_id).first()
            if session:
                session.last_seen = datetime.utcnow()
                session.route = route
                session.is_active = True
            else:
                session = self.UserSession(
                    user_id=user_id,
                    ip_address=ip_address,
                    route=route,
                    last_seen=datetime.utcnow(),
                    is_active=True
                )
                self.db.session.add(session)
            
            # Record page view
            page_view = self.PageView(
                route=route,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )
            self.db.session.add(page_view)
            
            self.db.session.commit()
            
        except Exception as e:
            logging.warning(f"Database tracking error: {str(e)}")
            db.session.rollback()
    
    def track_sale(self, customer_name, amount, customer_cpf=None, payment_id=None):
        """Track a new sale"""
        try:
            sale = self.Sale(
                customer_name=customer_name,
                customer_cpf=customer_cpf,
                amount=float(amount),
                payment_id=payment_id,
                payment_status='pending',
                created_at=datetime.utcnow()
            )
            self.db.session.add(sale)
            self.db.session.commit()
            
            logging.info(f"Sale tracked in database: {customer_name} - R$ {amount}")
            return sale
            
        except Exception as e:
            logging.warning(f"Database sale tracking error: {str(e)}")
            db.session.rollback()
            return None
    
    def update_sale_status(self, payment_id, status):
        """Update sale payment status"""
        try:
            sale = self.Sale.query.filter_by(payment_id=payment_id).first()
            if sale:
                sale.payment_status = status
                if status == 'completed':
                    sale.completed_at = datetime.utcnow()
                self.db.session.commit()
                return sale
        except Exception as e:
            logging.warning(f"Sale status update error: {str(e)}")
            db.session.rollback()
        return None
    
    def get_analytics_data(self):
        """Get current analytics data from database"""
        try:
            # Update today's stats
            analytics = self.AnalyticsData.update_today_stats()
            
            # Get active users (last 5 minutes)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            active_users = self.UserSession.query.filter(
                self.UserSession.last_seen >= five_minutes_ago,
                self.UserSession.is_active == True
            ).distinct(self.UserSession.user_id).count()
            
            # Get today's page views by route
            today = datetime.utcnow().date()
            page_views_by_route = self.db.session.query(
                self.PageView.route,
                func.count(self.PageView.id).label('count')
            ).filter(
                func.date(self.PageView.timestamp) == today
            ).group_by(self.PageView.route).all()
            
            page_views_dict = {route: count for route, count in page_views_by_route}
            
            # Get recent sales (last 10)
            recent_sales = self.Sale.query.filter(
                func.date(self.Sale.created_at) == today
            ).order_by(self.Sale.created_at.desc()).limit(10).all()
            
            recent_sales_list = []
            for sale in recent_sales:
                recent_sales_list.append({
                    'customerName': sale.customer_name,
                    'amount': float(sale.amount),
                    'timestamp': sale.created_at.strftime('%H:%M:%S'),
                    'status': sale.payment_status
                })
            
            return {
                'activeUsers': active_users,
                'pageViews': analytics.page_views if analytics else 0,
                'totalSales': analytics.total_sales if analytics else 0,
                'totalRevenue': float(analytics.total_revenue) if analytics else 0,
                'pageViewsByRoute': page_views_dict,
                'recentSales': recent_sales_list
            }
            
        except Exception as e:
            logging.error(f"Analytics data error: {str(e)}")
            return {
                'activeUsers': 0,
                'pageViews': 0,
                'totalSales': 0,
                'totalRevenue': 0,
                'pageViewsByRoute': {},
                'recentSales': []
            }
    
    def cleanup_old_data(self):
        """Clean up old session and page view data"""
        try:
            # Mark sessions older than 5 minutes as inactive
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            self.UserSession.query.filter(
                self.UserSession.last_seen < five_minutes_ago
            ).update({'is_active': False})
            
            # Delete page views older than 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            self.PageView.query.filter(
                self.PageView.timestamp < seven_days_ago
            ).delete()
            
            # Delete inactive sessions older than 1 day
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            self.UserSession.query.filter(
                self.UserSession.last_seen < one_day_ago,
                self.UserSession.is_active == False
            ).delete()
            
            self.db.session.commit()
            
        except Exception as e:
            logging.warning(f"Database cleanup error: {str(e)}")
            db.session.rollback()

# Global database analytics instance
db_analytics = DatabaseAnalytics()