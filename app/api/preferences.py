# app/api/preferences.py
"""
Preferences API Endpoints
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User

preferences_bp = Blueprint('preferences', __name__)


@preferences_bp.route('/get-preferences', methods=['GET'])
@jwt_required(optional=True)
def get_preferences():
    """Get user preferences"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify(user.preferences), 200
        
        # Default preferences
        return jsonify({
            'subtitle_font': 'Arial-Bold',
            'subtitle_size': 70,
            'whisper_model': 'base',
            'video_speed': 1.0,
            'num_clips': 3,
            'with_subtitles': True
        }), 200
    except Exception as e:
        print(f"Erro ao buscar preferências: {e}")
        return jsonify({
            'subtitle_font': 'Arial-Bold',
            'subtitle_size': 70,
            'whisper_model': 'base',
            'video_speed': 1.0,
            'num_clips': 3,
            'with_subtitles': True
        }), 200


@preferences_bp.route('/save-preferences', methods=['POST'])
@jwt_required()
def save_preferences():
    """Save user preferences"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        user.preferences.update(data)
        db.session.commit()
        
        return jsonify({"message": "Preferences saved"}), 200
    except Exception as e:
        print(f"Erro ao salvar preferências: {e}")
        return jsonify({"error": str(e)}), 500


@preferences_bp.route('/history', methods=['GET'])
@jwt_required(optional=True)
def get_history():
    """Get processing history"""
    return jsonify([]), 200


@preferences_bp.route('/analytics', methods=['GET'])
@jwt_required(optional=True)
def get_analytics():
    """Get analytics data"""
    return jsonify({
        'total_clips': 0,
        'avg_score': 0,
        'sessions': [],
        'avg_duration': 0,
        'keywords': [],
        'narratives': {'INTRODUCAO': 0, 'CONTEXTO': 0, 'CLIMAX': 0},
        'sentiments': {}
    }), 200