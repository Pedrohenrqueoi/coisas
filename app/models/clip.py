# -*- coding: utf-8 -*-
"""
Clip Model - CORRIGIDO
"""
from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON


class Clip(db.Model):
    """Clip model for generated video clips"""
    __tablename__ = 'clips'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False, index=True)
    
    # File info
    filename = db.Column(db.String(255), nullable=False)
    file_size_mb = db.Column(db.Float)
    file_path = db.Column(db.String(500))
    s3_key = db.Column(db.String(500))
    
    # Clip metadata
    start_time = db.Column(db.Float, nullable=False)  # seconds
    end_time = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    
    # AI scores
    relevance_score = db.Column(db.Integer, default=0)
    narrative_type = db.Column(db.String(20))  # INTRODUCAO, CONTEXTO, CLIMAX
    
    # Content
    transcription_text = db.Column(db.Text)
    social_media_caption = db.Column(db.Text)
    analytics_report = db.Column(db.Text)
    
    # ⚠️ MUDANÇA: metadata → clip_metadata
    clip_metadata = db.Column(JSON, default=lambda: {})
    
    # Stats
    downloads = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<Clip {self.id} from Video {self.video_id}>'
    
    def to_dict(self):
        """Serialize clip to dictionary"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'filename': self.filename,
            'file_size_mb': self.file_size_mb,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'relevance_score': self.relevance_score,
            'narrative_type': self.narrative_type,
            'transcription_text': self.transcription_text,
            'social_media_caption': self.social_media_caption,
            'downloads': self.downloads,
            'views': self.views,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'download_url': self.get_download_url()
        }
    
    def get_download_url(self):
        """Get URL to download clip"""
        if self.s3_key:
            from app.utils.file_handler import generate_s3_presigned_url
            return generate_s3_presigned_url(self.s3_key)
        else:
            return f'/api/clips/{self.id}/download'
    
    def increment_downloads(self):
        """Track download count"""
        self.downloads += 1
        db.session.commit()
    
    def increment_views(self):
        """Track view count"""
        self.views += 1
        db.session.commit()