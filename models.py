from datetime import datetime
from sqlalchemy import func
from app import db

class Registration(db.Model):
    __tablename__ = 'registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(14), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Registration {self.full_name}>'

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    route = db.Column(db.String(200))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, index=True)

class PageView(db.Model):
    __tablename__ = 'page_views'
    
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(200), nullable=False, index=True)
    user_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_agent = db.Column(db.Text)

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_cpf = db.Column(db.String(14), index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_id = db.Column(db.String(100), unique=True)
    payment_status = db.Column(db.String(20), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Sale {self.customer_name} - R$ {self.amount}>'

class AnalyticsData(db.Model):
    __tablename__ = 'analytics_data'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    active_users = db.Column(db.Integer, default=0)
    page_views = db.Column(db.Integer, default=0)
    total_sales = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def get_today_stats():
        today = datetime.utcnow().date()
        return AnalyticsData.query.filter_by(date=today).first()
    
    @staticmethod
    def update_today_stats():
        today = datetime.utcnow().date()
        analytics = AnalyticsData.query.filter_by(date=today).first()
        
        if not analytics:
            analytics = AnalyticsData(date=today)
            db.session.add(analytics)
        
        # Count active users (last 5 minutes)
        from datetime import timedelta
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        active_users = UserSession.query.filter(
            UserSession.last_seen >= five_minutes_ago,
            UserSession.is_active == True
        ).distinct(UserSession.user_id).count()
        
        # Count today's page views
        page_views = PageView.query.filter(
            func.date(PageView.timestamp) == today
        ).count()
        
        # Count today's sales
        today_sales = Sale.query.filter(
            func.date(Sale.created_at) == today,
            Sale.payment_status == 'completed'
        ).all()
        
        total_sales = len(today_sales)
        total_revenue = sum(float(sale.amount) for sale in today_sales)
        
        analytics.active_users = active_users
        analytics.page_views = page_views
        analytics.total_sales = total_sales
        analytics.total_revenue = total_revenue
        
        db.session.commit()
        return analytics


class CrasUnit(db.Model):
    __tablename__ = 'cras_units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False, index=True)
    postal_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CrasUnit {self.name} - {self.city}/{self.state}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email
        }
