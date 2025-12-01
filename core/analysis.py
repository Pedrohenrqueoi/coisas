# core/analysis.py
"""
Módulo de Análise de Vídeo e Áudio
"""
import librosa
import numpy as np
import moviepy.editor as mpy


def analyze_sentiment_from_audio(audio_path):
    """
    Analisa o sentimento do áudio baseado em energia e pitch
    Retorna um dicionário com análise básica
    """
    try:
        # Carrega o áudio
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Calcula energia RMS
        rms = librosa.feature.rms(y=y)[0]
        energy = np.mean(rms)
        
        # Calcula pitch médio
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
        
        # Classifica sentimento baseado em energia
        if energy > 0.1:
            sentiment = "URGENTE"
        elif energy > 0.05:
            sentiment = "ALERTA"
        else:
            sentiment = "NEUTRO"
        
        return {
            "sentiment": sentiment,
            "energy": float(energy),
            "pitch_mean": float(pitch_mean),
            "confidence": 0.75
        }
    except Exception as e:
        print(f"Erro na análise de sentimento: {e}")
        return {
            "sentiment": "NEUTRO",
            "energy": 0,
            "pitch_mean": 0,
            "confidence": 0
        }


def find_best_clips_auto(transcription, preferences, sentiment_data):
    """
    Encontra os melhores clipes automaticamente
    """
    num_clips = preferences.get('num_clips', 3)
    min_duration = preferences.get('min_duration', 30)
    max_duration = preferences.get('max_duration', 120)
    
    clips = []
    
    # Divide a transcrição em blocos
    segments = transcription if isinstance(transcription, list) else []
    
    if not segments:
        return []
    
    # Calcula duração total
    total_duration = segments[-1]['end'] if segments else 0
    
    # Divide em partes iguais
    clip_duration = min(max_duration, total_duration / num_clips)
    
    for i in range(num_clips):
        start = i * clip_duration
        end = min(start + clip_duration, total_duration)
        
        # Pega segmentos nesse intervalo
        clip_segments = [
            s for s in segments 
            if s['start'] >= start and s['end'] <= end
        ]
        
        text = " ".join(s['text'] for s in clip_segments)
        
        # Score baseado em palavras-chave
        score = 50 + (len(text.split()) * 2)
        score = min(100, score)
        
        # Tipo narrativo baseado na posição
        if i == 0:
            narrative = "INTRODUCAO"
        elif i == num_clips - 1:
            narrative = "CLIMAX"
        else:
            narrative = "CONTEXTO"
        
        clips.append({
            "start": start,
            "end": end,
            "duration": end - start,
            "segments": clip_segments,
            "text": text,
            "score": score,
            "narrative": narrative
        })
    
    return clips


def smart_crop(video_clip, target_aspect=(9, 16)):
    """
    Faz crop inteligente do vídeo para formato vertical
    """
    w, h = video_clip.size
    target_w, target_h = target_aspect
    
    # Calcula proporção alvo
    target_ratio = target_h / target_w
    current_ratio = h / w
    
    if current_ratio >= target_ratio:
        # Vídeo já é vertical, só ajusta largura
        new_w = int(h / target_ratio)
        x1 = (w - new_w) // 2
        return video_clip.crop(x1=x1, width=new_w)
    else:
        # Vídeo é horizontal, corta altura
        new_h = int(w * target_ratio)
        y1 = (h - new_h) // 2
        return video_clip.crop(y1=y1, height=new_h)