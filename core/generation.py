# core/generation.py
"""
Módulo de Geração de Conteúdo com IA
"""
import moviepy.editor as mpy


def generate_smart_caption(text, sentiment_data):
    """
    Gera legenda para redes sociais
    """
    sentiment = sentiment_data.get('sentiment', 'NEUTRO')
    
    # Emojis baseados em sentimento
    emoji_map = {
        'URGENTE': '🚨🔥',
        'ALERTA': '⚠️💥',
        'POSITIVO': '✨🎉',
        'NEUTRO': '📹'
    }
    
    emoji = emoji_map.get(sentiment, '📹')
    
    # Pega primeiras palavras
    words = text.split()[:15]
    summary = " ".join(words)
    
    caption = f"{emoji} {summary}...\n\n"
    caption += "#viral #conteudo #ia #videoediting"
    
    return caption


def generate_strategic_report(score, narrative, sentiment_data, clip_data, text):
    """
    Gera relatório estratégico do clipe
    """
    report = f"""
═══════════════════════════════════════
🤖 RELATÓRIO DE ANÁLISE IA
═══════════════════════════════════════

📊 SCORE GERAL: {score}/100
📖 TIPO: {narrative}
🎭 SENTIMENTO: {sentiment_data.get('sentiment', 'N/A')}

⏱️ DURAÇÃO: {clip_data.get('duration', 0):.1f}s
🎬 INÍCIO: {clip_data.get('start', 0):.1f}s
🎬 FIM: {clip_data.get('end', 0):.1f}s

📝 TRANSCRIÇÃO:
{text[:200]}...

💡 RECOMENDAÇÕES:
- Use hashtags relevantes
- Poste em horário de pico
- Adicione call-to-action

═══════════════════════════════════════
    """
    return report.strip()


def group_words_for_subtitles(words, clip_start, words_per_group=3):
    """
    Agrupa palavras para criar legendas dinâmicas
    """
    groups = []
    
    for i in range(0, len(words), words_per_group):
        group = words[i:i + words_per_group]
        
        if not group:
            continue
        
        text = " ".join(w.get('word', '') for w in group)
        start = group[0].get('start', 0)
        end = group[-1].get('end', start + 1)
        
        groups.append({
            'text': text.strip(),
            'start': start - clip_start,
            'duration': end - start
        })
    
    return groups


def create_subtitle_clip(text, duration, video_w, video_h, fontsize=70):
    """
    Cria um clipe de legenda com MoviePy
    """
    try:
        txt_clip = mpy.TextClip(
            text,
            fontsize=fontsize,
            color='white',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(video_w * 0.9, None),
            font='Arial-Bold'
        )
        
        txt_clip = txt_clip.set_position(('center', 0.8 * video_h))
        txt_clip = txt_clip.set_duration(duration)
        
        return txt_clip
    except Exception as e:
        print(f"Erro ao criar legenda: {e}")
        return None