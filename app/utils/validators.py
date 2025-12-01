# -*- coding: utf-8 -*-
"""
Input Validators
"""
import os
import mimetypes
from werkzeug.utils import secure_filename
import moviepy.editor as mpy


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_video_file(file, max_size_bytes):
    """
    Validate uploaded video file
    Returns: (is_valid, error_message, file_info)
    """
    if not file:
        return False, "No file provided", None
    
    if file.filename == '':
        return False, "Empty filename", None
    
    # Check extension
    from flask import current_app
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    if not allowed_file(file.filename, allowed_extensions):
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}", None
    
    # Check file size (basic check before full read)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"File too large (max {max_mb:.0f}MB)", None
    
    # Check MIME type
    mime_type = mimetypes.guess_type(file.filename)[0]
    if not mime_type or not mime_type.startswith('video/'):
        return False, "File does not appear to be a video", None
    
    file_info = {
        'original_filename': file.filename,
        'secure_filename': secure_filename(file.filename),
        'file_size': file_size,
        'file_size_mb': round(file_size / (1024 * 1024), 2),
        'mime_type': mime_type
    }
    
    return True, None, file_info


def validate_video_properties(video_path, user_plan_limits):
    """
    Validate video properties using MoviePy
    Returns: (is_valid, error_message, video_metadata)
    """
    try:
        with mpy.VideoFileClip(str(video_path)) as clip:
            duration = clip.duration
            width, height = clip.size
            fps = clip.fps
            
            # Check duration limits
            max_duration = user_plan_limits.get('max_video_duration', -1)
            if max_duration != -1 and duration > max_duration:
                return False, f"Video duration ({duration:.0f}s) exceeds plan limit ({max_duration}s)", None
            
            # Check minimum duration
            if duration < 5:
                return False, "Video too short (minimum 5 seconds)", None
            
            # Check resolution
            if width < 320 or height < 240:
                return False, "Video resolution too low (minimum 320x240)", None
            
            video_metadata = {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps,
                'has_audio': clip.audio is not None,
                'codec': getattr(clip.reader, 'infos', {}).get('video_codec', 'unknown')
            }
            
            return True, None, video_metadata
    
    except Exception as e:
        return False, f"Invalid video file: {str(e)}", None


def validate_clip_parameters(data, video_duration):
    """
    Validate clip cutting parameters
    Returns: (is_valid, error_message)
    """
    mode = data.get('mode', 'auto')
    
    if mode not in ['auto', 'manual']:
        return False, "Invalid mode (must be 'auto' or 'manual')"
    
    if mode == 'manual':
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time is None or end_time is None:
            return False, "start_time and end_time required for manual mode"
        
        try:
            start_time = float(start_time)
            end_time = float(end_time)
        except (ValueError, TypeError):
            return False, "start_time and end_time must be numbers"
        
        if start_time < 0 or end_time < 0:
            return False, "Times must be positive"
        
        if start_time >= end_time:
            return False, "start_time must be less than end_time"
        
        if end_time > video_duration:
            return False, f"end_time exceeds video duration ({video_duration:.1f}s)"
        
        if (end_time - start_time) < 5:
            return False, "Clip must be at least 5 seconds long"
    
    # Validate other parameters
    num_clips = data.get('num_clips', 3)
    try:
        num_clips = int(num_clips)
        if num_clips < 1 or num_clips > 10:
            return False, "num_clips must be between 1 and 10"
    except (ValueError, TypeError):
        return False, "num_clips must be an integer"
    
    return True, None