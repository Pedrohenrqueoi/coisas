# -*- coding: utf-8 -*-
"""
Video Processing Service
Refactored from core/processing.py
"""
import os
import torch
import whisper
import moviepy.editor as mpy
from pathlib import Path
from flask import current_app

from app.services.transcription_service import TranscriptionService
from app.services.subtitle_service import SubtitleService
from app.utils.file_handler import get_file_size_mb, download_from_s3
from core.analysis import (
    analyze_sentiment_from_audio,
    find_best_clips_auto,
    smart_crop
)
from core.generation import (
    generate_smart_caption,
    generate_strategic_report,
    group_words_for_subtitles,
    create_subtitle_clip
)


class VideoProcessor:
    """Orchestrates video processing pipeline"""
    
    def __init__(self, video, settings, user):
        """
        Args:
            video: Video model instance
            settings: Processing settings dict
            user: User model instance
        """
        self.video = video
        self.settings = settings
        self.user = user
        self.temp_dir = Path(current_app.config['TEMP_FOLDER'])
        self.done_dir = Path(current_app.config['DONE_FOLDER'])
        
        # Ensure folders exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)
        
        # Get video file path
        if video.s3_key:
            # Download from S3 if needed
            self.video_path = self.temp_dir / f"{video.id}_input.mp4"
            if not self.video_path.exists():
                download_from_s3(video.s3_key, self.video_path)
        else:
            self.video_path = Path(video.file_path)
    
    def extract_audio(self):
        """Extract audio from video"""
        audio_path = self.temp_dir / f"{self.video.id}_audio.wav"
        
        with mpy.VideoFileClip(str(self.video_path)) as clip:
            clip.audio.write_audiofile(
                str(audio_path),
                codec='pcm_s16le',
                fps=16000,
                logger=None
            )
        
        return audio_path
    
    def analyze_sentiment(self, audio_path):
        """Analyze audio sentiment"""
        return analyze_sentiment_from_audio(audio_path)
    
    def transcribe_audio(self, audio_path, callback=None):
        """Transcribe audio using Whisper"""
        model_name = self.settings.get('whisper_model', 'base')
        device = "cuda" if torch.cuda.is_available() and current_app.config.get('USE_GPU') else "cpu"
        
        model = whisper.load_model(model_name, device=device)
        
        with torch.no_grad():
            result = model.transcribe(
                str(audio_path),
                language="pt",
                verbose=False,
                word_timestamps=True
            )
        
        return result.get("segments", [])
    
    def find_best_clips(self, transcription, sentiment_data):
        """Find best clips using AI"""
        mode = self.settings.get('mode', 'auto')
        
        if mode == 'manual':
            return self._get_manual_clip(transcription)
        else:
            # Use plan limits
            from flask import current_app
            plan_limits = current_app.config['PLANS'][self.user.plan]
            
            preferences = {
                'min_duration': 30,
                'max_duration': 120,
                'num_clips': min(
                    self.settings.get('num_clips', 3),
                    plan_limits.get('max_clips_per_video', 3)
                )
            }
            
            return find_best_clips_auto(transcription, preferences, sentiment_data)
    
    def _get_manual_clip(self, transcription):
        """Create manual clip based on start/end times"""
        start_time = float(self.settings.get('start_time', 0))
        end_time = float(self.settings.get('end_time', 60))
        
        manual_segments = [
            s for s in transcription 
            if s['start'] < end_time and s['end'] > start_time
        ]
        
        manual_text = " ".join(s['text'] for s in manual_segments).strip()
        
        return [{
            "start": start_time,
            "end": end_time,
            "segments": manual_segments,
            "text": manual_text,
            "duration": end_time - start_time,
            "score": 99,
            "narrative": "MANUAL"
        }]
    
    def render_clip(self, clip_data, index):
        """Render a single clip with subtitles and effects"""
        with mpy.VideoFileClip(str(self.video_path)) as original_clip:
            # Extract clip segment
            part = original_clip.subclip(clip_data['start'], clip_data['end'])
            
            # Apply speed adjustment
            video_speed = float(self.settings.get('video_speed', 1.0))
            if video_speed != 1.0:
                part = part.fx(mpy.fx.speedx, video_speed)
            
            # Apply smart crop for vertical video
            part_vertical = smart_crop(part.without_audio())
            
            composition_clips = [part_vertical]
            
            # Add subtitles if enabled
            if self.settings.get('with_subtitles', True):
                subtitle_clips = self._generate_subtitle_clips(
                    clip_data,
                    part_vertical,
                    video_speed
                )
                composition_clips.extend(subtitle_clips)
            
            # Add watermark if provided
            watermark_path = self.settings.get('watermark_path')
            if watermark_path and Path(watermark_path).exists():
                watermark_clip = self._add_watermark(watermark_path, part_vertical.duration)
                composition_clips.append(watermark_clip)
            
            # Compose final video
            final_video = mpy.CompositeVideoClip(composition_clips, size=part_vertical.size)
            final_video = final_video.set_audio(part.audio)
            
            # Save
            output_filename = f"{self.video.filename.rsplit('.', 1)[0]}_clip{index}.mp4"
            output_path = self.done_dir / output_filename
            
            final_video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=24,
                verbose=False,
                logger=None,
                threads=4,
                preset='medium'
            )
            
            # Cleanup
            part.close()
            part_vertical.close()
            final_video.close()
            for clip in composition_clips[1:]:  # Don't close the base video twice
                try:
                    clip.close()
                except:
                    pass
        
        return str(output_path), output_filename
    
    def _generate_subtitle_clips(self, clip_data, video_clip, video_speed):
        """Generate subtitle clips"""
        subtitle_clips = []
        
        words_in_clip = [
            word for seg in clip_data['segments'] 
            if 'words' in seg 
            for word in seg['words']
        ]
        
        subtitle_groups = group_words_for_subtitles(
            words_in_clip,
            clip_data['start'],
            words_per_group=3
        )
        
        subtitle_size = self.settings.get('subtitle_size', 70)
        
        for sub_group in subtitle_groups:
            start_time_adjusted = sub_group['start'] / video_speed
            duration_adjusted = sub_group['duration'] / video_speed
            
            if start_time_adjusted >= video_clip.duration:
                continue
            
            subtitle_clip = create_subtitle_clip(
                sub_group['text'],
                duration_adjusted,
                video_clip.w,
                video_clip.h,
                fontsize=subtitle_size
            )
            
            if subtitle_clip:
                subtitle_clip = subtitle_clip.set_start(start_time_adjusted)
                subtitle_clips.append(subtitle_clip)
        
        return subtitle_clips
    
    def _add_watermark(self, watermark_path, duration):
        """Add watermark to video"""
        watermark = mpy.ImageClip(str(watermark_path))
        watermark = watermark.resize(width=int(1080 * 0.15))
        watermark = watermark.set_duration(duration)
        watermark = watermark.set_position(('right', 'top')).margin(right=20, top=20, opacity=0)
        watermark = watermark.set_opacity(0.7)
        return watermark
    
    def generate_social_caption(self, text, sentiment_data):
        """Generate social media caption"""
        return generate_smart_caption(text, sentiment_data)
    
    def generate_analytics_report(self, clip_data, sentiment_data):
        """Generate analytics report"""
        return generate_strategic_report(
            clip_data['score'],
            clip_data.get('narrative', 'CONTEXT'),
            sentiment_data,
            clip_data,
            clip_data['text']
        )
    
    def get_file_size(self, file_path):
        """Get file size in MB"""
        return get_file_size_mb(file_path)
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        # Delete temp audio
        audio_path = self.temp_dir / f"{self.video.id}_audio.wav"
        if audio_path.exists():
            audio_path.unlink()
        
        # Delete downloaded video if from S3
        if self.video.s3_key:
            input_path = self.temp_dir / f"{self.video.id}_input.mp4"
            if input_path.exists():
                input_path.unlink()