# -*- coding: utf-8 -*-
"""
Analytics Service
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import Video, Clip, User


class AnalyticsService:
    """Handle analytics calculations and reporting"""
    
    @staticmethod
    def record_processing(video, clips_data, sentiment_data):
        """Record video processing event for analytics"""
        # This could write to a separate analytics table or external service
        pass
    
    @staticmethod
    def get_user_stats(user_id):
        """Get comprehensive user statistics"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Count videos by status
        total_videos = user.videos.count()
        completed_videos = user.videos.filter_by(status='completed').count()
        failed_videos = user.videos.filter_by(status='failed').count()
        
        # Count total clips
        total_clips = db.session.query(func.count(Clip.id)).join(Video).filter(
            Video.user_id == user_id
        ).scalar()
        
        # Calculate average processing time
        avg_processing_time = db.session.query(
            func.avg(
                func.extract('epoch', Video.processing_completed_at - Video.processing_started_at)
            )
        ).filter(
            Video.user_id == user_id,
            Video.status == 'completed',
            Video.processing_started_at.isnot(None),
            Video.processing_completed_at.isnot(None)
        ).scalar()
        
        # Get recent activity
        recent_videos = user.videos.order_by(Video.created_at.desc()).limit(5).all()
        
        return {
            'total_videos': total_videos,
            'completed_videos': completed_videos,
            'failed_videos': failed_videos,
            'total_clips': total_clips,
            'videos_this_month': user.videos_processed_this_month,
            'storage_used_mb': user.storage_used_mb,
            'avg_processing_time_seconds': round(avg_processing_time or 0, 2),
            'recent_videos': [v.to_dict() for v in recent_videos]
        }
    
    @staticmethod
    def get_global_stats():
        """Get platform-wide statistics"""
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        total_videos = Video.query.count()
        total_clips = Clip.query.count()
        
        # Processing success rate
        completed = Video.query.filter_by(status='completed').count()
        failed = Video.query.filter_by(status='failed').count()
        success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0
        
        # Users by plan
        plan_distribution = db.session.query(
            User.plan,
            func.count(User.id)
        ).group_by(User.plan).all()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_videos': total_videos,
            'total_clips': total_clips,
            'success_rate': round(success_rate, 2),
            'plan_distribution': dict(plan_distribution)
        }
    
    @staticmethod
    def get_video_analytics(video_id):
        """Get detailed analytics for a specific video"""
        video = Video.query.get(video_id)
        if not video:
            return None
        
        clips = video.clips.all()
        
        # Calculate metrics
        total_duration = sum(c.duration for c in clips)
        avg_score = sum(c.relevance_score for c in clips) / len(clips) if clips else 0
        
        # Narrative distribution
        narrative_counts = {}
        for clip in clips:
            narrative = clip.narrative_type or 'CONTEXT'
            narrative_counts[narrative] = narrative_counts.get(narrative, 0) + 1
        
        # Most downloaded clip
        most_downloaded = max(clips, key=lambda c: c.downloads) if clips else None
        
        return {
            'video_id': video.id,
            'total_clips': len(clips),
            'total_duration': round(total_duration, 2),
            'avg_relevance_score': round(avg_score, 2),
            'narrative_distribution': narrative_counts,
            'sentiment': video.sentiment_data,
            'processing_time': video.get_processing_time(),
            'most_downloaded_clip': most_downloaded.to_dict() if most_downloaded else None,
            'clips': [c.to_dict() for c in clips]
        }
    
    @staticmethod
    def get_trending_keywords(user_id=None, days=30):
        """Get trending keywords from recent videos"""
        from collections import Counter
        
        query = Video.query.filter(
            Video.status == 'completed',
            Video.created_at >= datetime.utcnow() - timedelta(days=days)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        videos = query.all()
        
        # Extract keywords from transcriptions
        all_words = []
        for video in videos:
            if video.transcription:
                for segment in video.transcription:
                    text = segment.get('text', '')
                    words = text.lower().split()
                    # Filter meaningful words (>5 chars)
                    all_words.extend([w for w in words if len(w) > 5 and w.isalpha()])
        
        # Count and return top keywords
        word_counts = Counter(all_words)
        return word_counts.most_common(20)
    
    @staticmethod
    def get_usage_report(user_id, month=None, year=None):
        """Get monthly usage report for a user"""
        if not month or not year:
            now = datetime.utcnow()
            month = now.month
            year = now.year
        
        # Get videos processed in the specified month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        videos = Video.query.filter(
            Video.user_id == user_id,
            Video.created_at >= start_date,
            Video.created_at < end_date
        ).all()
        
        # Calculate metrics
        total_videos = len(videos)
        completed_videos = sum(1 for v in videos if v.status == 'completed')
        failed_videos = sum(1 for v in videos if v.status == 'failed')
        
        total_clips = sum(v.clips.count() for v in videos)
        total_processing_time = sum(
            v.get_processing_time() or 0 for v in videos 
            if v.status == 'completed'
        )
        
        return {
            'month': month,
            'year': year,
            'total_videos': total_videos,
            'completed_videos': completed_videos,
            'failed_videos': failed_videos,
            'total_clips': total_clips,
            'total_processing_time_seconds': round(total_processing_time, 2),
            'videos': [v.to_dict() for v in videos]
        }