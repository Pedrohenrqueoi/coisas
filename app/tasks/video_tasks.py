# -*- coding: utf-8 -*-
"""
Celery Tasks for Video Processing
"""
import os
import traceback
from pathlib import Path
from celery import Task
from app import celery, db
from app.models import Video, Clip, User
from app.services.video_processor import VideoProcessor
from app.services.analytics_service import AnalyticsService


class VideoProcessingTask(Task):
    """Base task with error handling"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        video_id = args[0] if args else None
        if video_id:
            video = Video.query.get(video_id)
            if video:
                video.mark_as_failed(str(exc))
        
        # Log to monitoring system
        print(f"Task {task_id} failed: {exc}")
        traceback.print_exc()


@celery.task(base=VideoProcessingTask, bind=True, name='tasks.process_video')
def process_video_task(self, video_id, settings):
    """
    Main video processing task
    
    Args:
        video_id: Database ID of video
        settings: Processing settings dict
    """
    try:
        # Update task progress
        self.update_state(state='PROGRESS', meta={'stage': 'Starting', 'progress': 0})
        
        # Get video from database
        video = Video.query.get(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        # Mark as processing
        video.mark_as_processing(self.request.id)
        
        # Get user for plan limits
        user = video.user
        
        # Initialize processor
        processor = VideoProcessor(video, settings, user)
        
        # Step 1: Extract audio (5%)
        self.update_state(state='PROGRESS', meta={'stage': 'Extracting audio', 'progress': 5})
        audio_path = processor.extract_audio()
        
        # Step 2: Analyze sentiment (15%)
        self.update_state(state='PROGRESS', meta={'stage': 'Analyzing sentiment', 'progress': 15})
        sentiment_data = processor.analyze_sentiment(audio_path)
        video.sentiment_data = sentiment_data
        db.session.commit()
        
        # Step 3: Transcribe with Whisper (40%)
        self.update_state(state='PROGRESS', meta={'stage': 'Transcribing', 'progress': 30})
        transcription = processor.transcribe_audio(audio_path, 
                                                   callback=lambda p: self.update_state(
                                                       state='PROGRESS',
                                                       meta={'stage': 'Transcribing', 'progress': 30 + int(p * 0.1)}
                                                   ))
        video.transcription = transcription
        db.session.commit()
        
        # Step 4: Find best clips (50%)
        self.update_state(state='PROGRESS', meta={'stage': 'Finding clips', 'progress': 50})
        selected_clips = processor.find_best_clips(transcription, sentiment_data)
        
        # Step 5: Render clips (50-90%)
        total_clips = len(selected_clips)
        for idx, clip_data in enumerate(selected_clips, 1):
            progress = 50 + int((idx / total_clips) * 40)
            self.update_state(state='PROGRESS', meta={
                'stage': f'Rendering clip {idx}/{total_clips}',
                'progress': progress
            })
            
            # Render clip
            clip_path, clip_filename = processor.render_clip(clip_data, idx)
            
            # Save to database
            clip = Clip(
                video_id=video.id,
                filename=clip_filename,
                file_path=clip_path,
                file_size_mb=processor.get_file_size(clip_path),
                start_time=clip_data['start'],
                end_time=clip_data['end'],
                duration=clip_data['duration'],
                relevance_score=clip_data['score'],
                narrative_type=clip_data.get('narrative', 'CONTEXT'),
                transcription_text=clip_data['text']
            )
            
            # Generate social media content
            clip.social_media_caption = processor.generate_social_caption(
                clip_data['text'], 
                sentiment_data
            )
            
            clip.analytics_report = processor.generate_analytics_report(
                clip_data, 
                sentiment_data
            )
            
            db.session.add(clip)
        
        db.session.commit()
        
        # Step 6: Cleanup and finalize (95%)
        self.update_state(state='PROGRESS', meta={'stage': 'Finalizing', 'progress': 95})
        processor.cleanup_temp_files()
        
        # Mark as completed
        video.mark_as_completed()
        
        # Update user stats
        user.increment_usage()
        
        # Save analytics
        AnalyticsService.record_processing(video, selected_clips, sentiment_data)
        
        # Final update (100%)
        self.update_state(state='SUCCESS', meta={'stage': 'Completed', 'progress': 100})
        
        return {
            'video_id': video.id,
            'clips_generated': len(selected_clips),
            'status': 'completed'
        }
    
    except Exception as e:
        # Handle errors
        if video_id:
            video = Video.query.get(video_id)
            if video:
                video.mark_as_failed(str(e))
        
        raise


@celery.task(name='tasks.reset_monthly_usage')
def reset_monthly_usage_task():
    """
    Scheduled task to reset monthly usage counters
    Run on the 1st of each month
    """
    try:
        users = User.query.all()
        for user in users:
            user.reset_monthly_usage()
        
        return f"Reset usage for {len(users)} users"
    
    except Exception as e:
        print(f"Error resetting monthly usage: {e}")
        raise


@celery.task(name='tasks.cleanup_old_files')
def cleanup_old_files_task(days=7):
    """
    Scheduled task to cleanup old temporary files
    Run daily
    """
    from app.utils.file_handler import cleanup_old_files
    from flask import current_app
    
    try:
        temp_folder = Path(current_app.config['TEMP_FOLDER'])
        deleted_count = cleanup_old_files(temp_folder, days)
        
        return f"Deleted {deleted_count} old files"
    
    except Exception as e:
        print(f"Error cleaning up files: {e}")
        raise


@celery.task(name='tasks.send_processing_complete_email')
def send_processing_complete_email_task(user_id, video_id):
    """
    Send email notification when processing is complete
    """
    try:
        user = User.query.get(user_id)
        video = Video.query.get(video_id)
        
        if not user or not video:
            return
        
        # Send email via SendGrid
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        from flask import current_app
        
        message = Mail(
            from_email=current_app.config['FROM_EMAIL'],
            to_emails=user.email,
            subject='Your video is ready!',
            html_content=f"""
                <h2>Processing Complete!</h2>
                <p>Your video "{video.original_filename}" has been processed successfully.</p>
                <p>Generated {video.clips.count()} clips.</p>
                <p><a href="{current_app.config['BASE_URL']}/videos/{video.id}">View Results</a></p>
            """
        )
        
        sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
        response = sg.send(message)
        
        return f"Email sent to {user.email}"
    
    except Exception as e:
        print(f"Error sending email: {e}")
        # Don't raise - email failure shouldn't fail the task