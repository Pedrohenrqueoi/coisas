# -*- coding: utf-8 -*-
"""
Video Model
"""
from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON


class Video(db.Model):
    """Video model for uploaded videos"""
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # File info
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size_mb = db.Column(db.Float, nullable=False)
    file_path = db.Column(db.String(500))
    s3_key = db.Column(db.String(500))  # If using S3
    
    # Video metadata
    duration = db.Column(db.Float)  # seconds
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    fps = db.Column(db.Float)
    codec = db.Column(db.String(50))
    
    # Processing info
    status = db.Column(db.String(20), default='uploaded', nullable=False, index=True)
    # Status values: uploaded, queued, processing, completed, failed
    
    processing_mode = db.Column(db.String(20))  # auto, manual
    error_message = db.Column(db.Text)
    
    # Celery task
    task_id = db.Column(db.String(100), index=True)
    
    # AI Analysis
    transcription = db.Column(JSON)  # Full Whisper output
    sentiment_data = db.Column(JSON)
    
    # Processing settings used
    settings = db.Column(JSON, default=lambda: {
        'whisper_model': 'base',
        'with_subtitles': True,
        'subtitle_size': 70,
        'num_clips': 3
    })
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    processing_started_at = db.Column(db.DateTime)
    processing_completed_at = db.Column(db.DateTime)
    
    # Relationships
    clips = db.relationship('Clip', backref='video', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Video {self.id}: {self.original_filename}>'
    
    def to_dict(self, include_clips=False):
        """Serialize video to dictionary"""
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size_mb': self.file_size_mb,
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'status': self.status,
            'processing_mode': self.processing_mode,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processing_time': self.get_processing_time(),
            'clips_count': self.clips.count()
        }
        
        if include_clips:
            data['clips'] = [clip.to_dict() for clip in self.clips.all()]
        
        return data
    
    def get_processing_time(self):
        """Calculate processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return round(delta.total_seconds(), 2)
        return None
    
    def mark_as_processing(self, task_id):
        """Update status when processing starts"""
        self.status = 'processing'
        self.task_id = task_id
        self.processing_started_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_completed(self):
        """Update status when processing completes"""
        self.status = 'completed'
        self.processing_completed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_failed(self, error_message):
        """Update status when processing fails"""
        self.status = 'failed'
        self.error_message = error_message
        self.processing_completed_at = datetime.utcnow()
        db.session.commit()
    
    def get_download_url(self):
        """Get URL to download video"""
        if self.s3_key:
            # Return S3 presigned URL
            from app.utils.file_handler import generate_s3_presigned_url
            return generate_s3_presigned_url(self.s3_key)
        else:
            # Return local file URL
            return f'/api/videos/{self.id}/download'