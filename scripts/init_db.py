#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initialize Database with sample data
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User

def init_database():
    """Initialize database with default data"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Create tables
        print("Creating database tables...")
        db.create_all()
        
        # Create admin user
        admin_email = "admin@binhocut.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            print(f"Creating admin user: {admin_email}")
            admin = User(
                email=admin_email,
                username="admin",
                full_name="Admin User",
                plan="enterprise"
            )
            admin.set_password("admin123")  # CHANGE IN PRODUCTION!
            admin.is_admin = True  # You'll need to add this field to User model
            
            db.session.add(admin)
        
        # Create demo user
        demo_email = "demo@binhocut.com"
        demo = User.query.filter_by(email=demo_email).first()
        
        if not demo:
            print(f"Creating demo user: {demo_email}")
            demo = User(
                email=demo_email,
                username="demo",
                full_name="Demo User",
                plan="pro"
            )
            demo.set_password("demo123")
            
            db.session.add(demo)
        
        db.session.commit()
        
        print("✓ Database initialized successfully!")
        print(f"\nAdmin credentials:")
        print(f"  Email: {admin_email}")
        print(f"  Password: admin123")
        print(f"\nDemo credentials:")
        print(f"  Email: {demo_email}")
        print(f"  Password: demo123")
        print(f"\n⚠️  CHANGE DEFAULT PASSWORDS IN PRODUCTION!")


if __name__ == '__main__':
    init_database()