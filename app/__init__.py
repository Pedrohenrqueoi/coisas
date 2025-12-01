# -*- coding: utf-8 -*-
"""
Flask Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
celery = Celery(__name__)


def create_app(config_name='development'):
    """Application Factory Pattern"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    if config_name == 'production':
        from config.production import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from config.testing import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from config.development import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize Sentry
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    CORS(app)
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.videos import videos_bp
    from app.api.clips import clips_bp
    from app.api.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(clips_bp, url_prefix='/api/clips')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    # Register main routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {"error": "Internal server error"}, 500
    
    # Health check
    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "database": check_db_connection()
        }
    
    return app


def check_db_connection():
    """Check if database is accessible"""
    try:
        db.session.execute('SELECT 1')
        return "connected"
    except Exception:
        return "disconnected"