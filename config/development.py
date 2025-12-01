# -*- coding: utf-8 -*-
"""
Development Configuration
"""
import os
from datetime import timedelta

class DevelopmentConfig:
    """Development environment configuration"""
    
    # Flask
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URL',
    'sqlite:///binhocut.db'  # Banco local, não precisa instalar PostgreSQL
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Celery
   # CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
   # CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'America/Recife'
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # File Upload
    UPLOAD_FOLDER = os.path.abspath('./uploads')
    DONE_FOLDER = os.path.abspath('./done')
    TEMP_FOLDER = os.path.abspath('./temp')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
    
    # AI Models
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')
    WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cpu')
    USE_GPU = os.getenv('USE_GPU', 'false').lower() == 'true'
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    USE_S3 = all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME])
    
    # Stripe
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Email
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@binhocut.com')
    
    # Sentry
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    
    # Subscription Plans
    PLANS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'videos_per_month': 5,
            'max_video_duration': 600,  # 10 minutes
            'max_clips_per_video': 3,
            'features': ['basic_subtitles', 'manual_cut']
        },
        'pro': {
            'name': 'Pro',
            'price': 29.99,
            'videos_per_month': 50,
            'max_video_duration': 3600,  # 1 hour
            'max_clips_per_video': 10,
            'features': ['advanced_subtitles', 'auto_cut', 'watermark', 'hd_export']
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 99.99,
            'videos_per_month': -1,  # Unlimited
            'max_video_duration': -1,
            'max_clips_per_video': -1,
            'features': ['all', 'api_access', 'priority_support', 'custom_branding']
        }
    }