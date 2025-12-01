# -*- coding: utf-8 -*-
"""
Clips API Endpoints
"""
from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from pathlib import Path
import zipfile
import io

from app import db
from app.models import Clip, Video

clips_bp = Blueprint('clips', __name__)


@clips_bp.route('/<int:clip_id>', methods=['GET'])
@jwt_required()
def get_clip(clip_id):
    """Get clip details"""
    user_id = get_jwt_identity()
    clip = Clip.query.get(clip_id)
    
    if not clip:
        return jsonify({"error": "Clip not found"}), 404
    
    if clip.video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Track view
    clip.increment_views()
    
    return jsonify({
        "clip": clip.to_dict()
    }), 200


@clips_bp.route('/<int:clip_id>/download', methods=['GET'])
@jwt_required()
def download_clip(clip_id):
    """Download clip file"""
    user_id = get_jwt_identity()
    clip = Clip.query.get(clip_id)
    
    if not clip:
        return jsonify({"error": "Clip not found"}), 404
    
    if clip.video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Track download
    clip.increment_downloads()
    
    if clip.s3_key:
        # Return S3 presigned URL
        url = clip.get_download_url()
        return jsonify({"download_url": url}), 200
    elif clip.file_path and Path(clip.file_path).exists():
        # Serve local file
        return send_file(
            clip.file_path,
            as_attachment=True,
            download_name=clip.filename
        )
    else:
        return jsonify({"error": "File not found"}), 404


@clips_bp.route('/<int:clip_id>/caption', methods=['GET'])
@jwt_required()
def get_clip_caption(clip_id):
    """Get social media caption for clip"""
    user_id = get_jwt_identity()
    clip = Clip.query.get(clip_id)
    
    if not clip:
        return jsonify({"error": "Clip not found"}), 404
    
    if clip.video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "caption": clip.social_media_caption,
        "transcription": clip.transcription_text
    }), 200


@clips_bp.route('/<int:clip_id>/analytics', methods=['GET'])
@jwt_required()
def get_clip_analytics(clip_id):
    """Get analytics report for clip"""
    user_id = get_jwt_identity()
    clip = Clip.query.get(clip_id)
    
    if not clip:
        return jsonify({"error": "Clip not found"}), 404
    
    if clip.video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "analytics_report": clip.analytics_report,
        "relevance_score": clip.relevance_score,
        "narrative_type": clip.narrative_type,
        "downloads": clip.downloads,
        "views": clip.views
    }), 200


@clips_bp.route('/<int:clip_id>', methods=['DELETE'])
@jwt_required()
def delete_clip(clip_id):
    """Delete a clip"""
    user_id = get_jwt_identity()
    clip = Clip.query.get(clip_id)
    
    if not clip:
        return jsonify({"error": "Clip not found"}), 404
    
    if clip.video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Delete file
    from app.utils.file_handler import delete_file
    if clip.file_path or clip.s3_key:
        delete_file(clip.file_path, clip.s3_key)
    
    # Delete from database
    db.session.delete(clip)
    db.session.commit()
    
    return jsonify({
        "message": "Clip deleted successfully"
    }), 200


@clips_bp.route('/video/<int:video_id>/download-all', methods=['GET'])
@jwt_required()
def download_all_clips(video_id):
    """Download all clips from a video as ZIP"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    clips = video.clips.all()
    
    if not clips:
        return jsonify({"error": "No clips found"}), 404
    
    # Create ZIP in memory
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for clip in clips:
            if clip.file_path and Path(clip.file_path).exists():
                # Add video file
                zf.write(clip.file_path, arcname=clip.filename)
                
                # Add caption file
                caption_filename = clip.filename.replace('.mp4', '_caption.txt')
                zf.writestr(caption_filename, clip.social_media_caption or '')
                
                # Add analytics file
                analytics_filename = clip.filename.replace('.mp4', '_analytics.txt')
                zf.writestr(analytics_filename, clip.analytics_report or '')
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{video.filename.rsplit(".", 1)[0]}_clips.zip'
    )