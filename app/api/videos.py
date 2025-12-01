# -*- coding: utf-8 -*-
"""
Videos API Endpoints
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import moviepy.editor as mpy
from pathlib import Path

from app import db, limiter
from app.models import Video, User
from app.utils.validators import validate_video_file, validate_video_properties, validate_clip_parameters
from app.utils.file_handler import save_uploaded_file
from app.utils.decorators import check_usage_limit
from app.tasks.video_tasks import process_video_task

videos_bp = Blueprint('videos', __name__)


@videos_bp.route('/upload', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
@check_usage_limit('video')
def upload_video():
    """Upload a video file"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    
    # Validate file
    from flask import current_app
    is_valid, error, file_info = validate_video_file(
        file,
        current_app.config['MAX_CONTENT_LENGTH']
    )
    
    if not is_valid:
        return jsonify({"error": error}), 400
    
    # Save file
    file_path, s3_key = save_uploaded_file(file, user_id, folder='videos')
    
    # Validate video properties
    path_to_check = file_path if file_path else Path(current_app.config['TEMP_FOLDER']) / file_info['secure_filename']
    
    from flask import current_app
    plan_limits = current_app.config['PLANS'][user.plan]
    
    is_valid, error, video_metadata = validate_video_properties(
        path_to_check if file_path else file_path,
        plan_limits
    )
    
    if not is_valid:
        return jsonify({"error": error}), 400
    
    # Create video record
    video = Video(
        user_id=user_id,
        filename=file_info['secure_filename'],
        original_filename=file_info['original_filename'],
        file_size_mb=file_info['file_size_mb'],
        file_path=file_path,
        s3_key=s3_key,
        duration=video_metadata['duration'],
        width=video_metadata['width'],
        height=video_metadata['height'],
        fps=video_metadata['fps'],
        codec=video_metadata['codec'],
        status='uploaded'
    )
    
    db.session.add(video)
    db.session.commit()
    
    return jsonify({
        "message": "Video uploaded successfully",
        "video": video.to_dict()
    }), 201


@videos_bp.route('/<int:video_id>/process', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def process_video(video_id):
    """Start processing a video"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    if video.status not in ['uploaded', 'failed']:
        return jsonify({"error": f"Video already {video.status}"}), 400
    
    # Get processing settings
    settings = request.get_json() or {}
    
    # Validate settings
    is_valid, error = validate_clip_parameters(settings, video.duration)
    if not is_valid:
        return jsonify({"error": error}), 400
    
    # Merge with user preferences
    user = User.query.get(user_id)
    default_settings = user.preferences.copy()
    default_settings.update(settings)
    
    # Save settings to video
    video.settings = default_settings
    video.status = 'queued'
    db.session.commit()
    
    # Queue processing task
    task = process_video_task.delay(video.id, default_settings)
    
    video.task_id = task.id
    db.session.commit()
    
    return jsonify({
        "message": "Processing started",
        "video_id": video.id,
        "task_id": task.id
    }), 202


@videos_bp.route('/<int:video_id>/status', methods=['GET'])
@jwt_required()
def get_video_status(video_id):
    """Get processing status of a video"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    response = {
        "video_id": video.id,
        "status": video.status,
        "error_message": video.error_message
    }
    
    # If processing, get task status
    if video.task_id and video.status == 'processing':
        from celery.result import AsyncResult
        task = AsyncResult(video.task_id)
        
        response['task_status'] = task.state
        
        if task.state == 'PROGRESS':
            response['progress'] = task.info.get('progress', 0)
            response['stage'] = task.info.get('stage', 'Processing')
    
    # If completed, include clips
    if video.status == 'completed':
        response['clips'] = [clip.to_dict() for clip in video.clips.all()]
    
    return jsonify(response), 200


@videos_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_videos():
    """Get all videos for current user"""
    user_id = get_jwt_identity()
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    status = request.args.get('status')
    
    query = Video.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Video.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        "videos": [v.to_dict() for v in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages
    }), 200


@videos_bp.route('/<int:video_id>', methods=['GET'])
@jwt_required()
def get_video(video_id):
    """Get video details"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "video": video.to_dict(include_clips=True)
    }), 200


@videos_bp.route('/<int:video_id>', methods=['DELETE'])
@jwt_required()
def delete_video(video_id):
    """Delete a video and its clips"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Delete files
    from app.utils.file_handler import delete_file
    
    if video.file_path or video.s3_key:
        delete_file(video.file_path, video.s3_key)
    
    # Delete clip files
    for clip in video.clips:
        if clip.file_path or clip.s3_key:
            delete_file(clip.file_path, clip.s3_key)
    
    # Delete from database (cascade will handle clips)
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({
        "message": "Video deleted successfully"
    }), 200


@videos_bp.route('/<int:video_id>/download', methods=['GET'])
@jwt_required()
def download_video(video_id):
    """Download original video file"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    if video.s3_key:
        # Return S3 presigned URL
        url = video.get_download_url()
        return jsonify({"download_url": url}), 200
    elif video.file_path and Path(video.file_path).exists():
        # Serve local file
        return send_file(
            video.file_path,
            as_attachment=True,
            download_name=video.original_filename
        )
    else:
        return jsonify({"error": "File not found"}), 404


@videos_bp.route('/<int:video_id>/preview', methods=['GET'])
@jwt_required()
def get_video_preview(video_id):
    """Get video metadata for preview"""
    user_id = get_jwt_identity()
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
    
    if video.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify({
        "filename": video.filename,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "fps": video.fps,
        "file_size_mb": video.file_size_mb
    }), 200