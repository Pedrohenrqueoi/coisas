# Módulo: subtitle_service.py
import os
from moviepy.editor import TextClip, CompositeVideoClip

class SubtitleService:
    def __init__(self):
        pass

    def create_subtitle_clips(self, segments, video_w, video_h, fontsize=40, color='white', font='Arial'):
        """
        Cria clipes de texto para cada segmento da transcrição.
        Retorna uma lista de TextClips do MoviePy.
        """
        subtitle_clips = []
        
        # Margem de segurança para o texto não colar na borda
        text_width = video_w * 0.9

        for segment in segments:
            start = segment['start']
            end = segment['end']
            text = segment['text'].strip()

            if not text:
                continue

            # Cria o clipe de texto
            # method='caption' faz o texto quebrar linha automaticamente
            txt_clip = (TextClip(text, 
                               fontsize=fontsize, 
                               font=font, 
                               color=color, 
                               size=(text_width, None), 
                               method='caption')
                        .set_position(('center', 0.8 * video_h)) # Posição: 80% da altura (parte de baixo)
                        .set_start(start)
                        .set_duration(end - start))
            
            subtitle_clips.append(txt_clip)

        return subtitle_clips

    def generate_srt(self, segments, output_path):
        """
        Gera um arquivo de legendas padrão (.srt)
        """
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            milliseconds = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, start=1):
                start = format_time(segment['start'])
                end = format_time(segment['end'])
                text = segment['text'].strip()
                
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
        
        return output_path