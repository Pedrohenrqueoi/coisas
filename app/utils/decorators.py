# -*- coding: utf-8 -*-
"""
Custom Decorators
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User


def plan_required(*allowed_plans):
    """
    Decorator to restrict endpoint access by subscription plan
    Usage: @plan_required('pro', 'enterprise')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            if user.plan not in allowed_plans:
                return jsonify({
                    "error": "Upgrade required",
                    "message": f"This feature requires {' or '.join(allowed_plans)} plan",
                    "current_plan": user.plan,
                    "required_plans": list(allowed_plans)
                }), 403
            
            return fn(*args, **kwargs)
        
        return wrapper
    return decorator


def check_usage_limit(resource_type='video'):
    """
    Decorator to check if user has remaining quota
    Usage: @check_usage_limit('video')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            if resource_type == 'video':
                can_process, message = user.can_process_video()
                if not can_process:
                    return jsonify({
                        "error": "Quota exceeded",
                        "message": message,
                        "videos_used": user.videos_processed_this_month,
                        "upgrade_url": "/pricing"
                    }), 429
            
            return fn(*args, **kwargs)
        
        return wrapper
    return decorator


def admin_required(fn):
    """
    Decorator to restrict endpoint to admin users only
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has admin flag (you'd add this to User model)
        if not getattr(user, 'is_admin', False):
            return jsonify({"error": "Admin access required"}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper