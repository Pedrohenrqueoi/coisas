import os
import whisper
import torch

class TranscriptionService:
    def __init__(self, model_name="base"):
        """
        Inicializa o serviço de transcrição
        model_name: "tiny", "base", "small", "medium", "large"
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🤖 Carregando modelo Whisper ({model_name}) no dispositivo: {self.device}...")
        
        try:
            self.model = whisper.load_model(model_name, device=self.device)
        except Exception as e:
            print(f"⚠️ Erro ao carregar modelo na GPU, tentando CPU: {str(e)}")
            self.device = "cpu"
            self.model = whisper.load_model(model_name, device="cpu")

    def transcribe(self, audio_path):
        """
        Transcreve um arquivo de áudio para texto e segmentos
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")

        print(f"🎙️ Transcrevendo: {audio_path}")
        
        # Realiza a transcrição
        result = self.model.transcribe(audio_path)
        
        return {
            "text": result["text"],
            "segments": result["segments"], # Útil para saber o tempo de cada fala
            "language": result["language"]
        }