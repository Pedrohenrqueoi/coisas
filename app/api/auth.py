# -*- coding: utf-8 -*-
"""
Authentication API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db, limiter
from app.models import User
from datetime import datetime
import validators

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
    
    if not email or not validators.email(email):
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


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login user"""
    data = request.get_json()
    
    email_or_username = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email_or_username or not password:
        return jsonify({"error": "Email/username and password required"}), 400
    
    # Find user by email or username
    user = User.query.filter(
        (User.email == email_or_username) | (User.username == email_or_username)
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    
    return jsonify({
        "access_token": access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'full_name' in data:
        user.full_name = data['full_name'].strip()
    
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    if 'preferences' in data and isinstance(data['preferences'], dict):
        user.preferences.update(data['preferences'])
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "message": "Profile updated successfully",
        "user": user.to_dict()
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("3 per hour")
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not user.check_password(old_password):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({
        "message": "Password changed successfully"
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (token blacklisting would go here)"""
    # In production, implement token blacklisting with Redis
    return jsonify({
        "message": "Logged out successfully"
    }), 200