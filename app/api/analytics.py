# -*- coding: utf-8 -*-
"""
Analytics API Endpoints
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.analytics_service import AnalyticsService
from app.utils.decorators import admin_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get user dashboard analytics"""
    user_id = get_jwt_identity()
    
    stats = AnalyticsService.get_user_stats(user_id)
    
    if not stats:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(stats), 200


@analytics_bp.route('/video/<int:video_id>', methods=['GET'])
@jwt_required()
def get_video_analytics(video_id):
    """Get analytics for a specific video"""
    from app.models import Video
    
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    analytics = AnalyticsService.get_video_analytics(video_id)
    
    if not analytics:
        return jsonify({"error": "Analytics not available"}), 404
    
    return jsonify(analytics), 200


@analytics_bp.route('/keywords', methods=['GET'])
@jwt_required()
def get_trending_keywords():
    """Get trending keywords from user's videos"""
    user_id = get_jwt_identity()
    
    days = request.args.get('days', 30, type=int)
    
    keywords = AnalyticsService.get_trending_keywords(user_id, days)
    
    return jsonify({
        "keywords": [
            {"word": word, "count": count}
            for word, count in keywords
        ]
    }), 200


@analytics_bp.route('/usage-report', methods=['GET'])
@jwt_required()
def get_usage_report():
    """Get monthly usage report"""
    user_id = get_jwt_identity()
    
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    report = AnalyticsService.get_usage_report(user_id, month, year)
    
    return jsonify(report), 200


@analytics_bp.route('/global', methods=['GET'])
@jwt_required()
@admin_required
def get_global_analytics():
    """Get platform-wide analytics (admin only)"""
    stats = AnalyticsService.get_global_stats()
    
    return jsonify(stats), 200