# app/api/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db, limiter
from app.models import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate input
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    
    # Validação simples de email
    if not email or '@' not in email or '.' not in email:
        return jsonify({"error": "Invalid email address"}), 400
    
    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    if not password or len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    
    # Create user
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        plan='free'
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 201


# ... resto do código permanece igual