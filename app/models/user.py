# -*- coding: utf-8 -*-
"""
User Model
"""
from datetime import datetime
from app import db, bcrypt
from sqlalchemy.dialects.postgresql import JSON


class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile
    full_name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(255))
    
    # Subscription
    plan = db.Column(db.String(20), default='free', nullable=False)
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100))
    subscription_status = db.Column(db.String(20), default='active')
    subscription_end_date = db.Column(db.DateTime)
    
    # Usage tracking
    videos_processed_this_month = db.Column(db.Integer, default=0)
    total_videos_processed = db.Column(db.Integer, default=0)
    storage_used_mb = db.Column(db.Float, default=0.0)
    
    # Settings
    preferences = db.Column(JSON, default=lambda: {
        'subtitle_font': 'Arial-Bold',
        'subtitle_size': 70,
        'whisper_model': 'base',
        'default_aspect_ratio': '9:16'
    })
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    videos = db.relationship('Video', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Serialize user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'plan': self.plan,
            'subscription_status': self.subscription_status,
            'videos_processed_this_month': self.videos_processed_this_month,
            'total_videos_processed': self.total_videos_processed,
            'storage_used_mb': self.storage_used_mb,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'preferences': self.preferences
        }
        
        if include_sensitive:
            data['stripe_customer_id'] = self.stripe_customer_id
            data['subscription_end_date'] = self.subscription_end_date.isoformat() if self.subscription_end_date else None
        
        return data
    
    def can_process_video(self, video_duration_seconds=None):
        """Check if user can process a new video"""
        from flask import current_app
        
        plan_limits = current_app.config['PLANS'][self.plan]
        
        # Check monthly limit
        monthly_limit = plan_limits['videos_per_month']
        if monthly_limit != -1 and self.videos_processed_this_month >= monthly_limit:
            return False, f"Monthly limit reached ({monthly_limit} videos)"
        
        # Check video duration
        if video_duration_seconds:
            max_duration = plan_limits['max_video_duration']
            if max_duration != -1 and video_duration_seconds > max_duration:
                return False, f"Video too long (max {max_duration}s for {self.plan} plan)"
        
        # Check subscription status
        if self.subscription_status not in ['active', 'trialing']:
            return False, "Subscription inactive"
        
        return True, "OK"
    
    def increment_usage(self):
        """Increment video processing counter"""
        self.videos_processed_this_month += 1
        self.total_videos_processed += 1
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly counter (called by scheduled task)"""
        self.videos_processed_this_month = 0
        db.session.commit()