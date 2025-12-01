// static/js/modules/api.js

import { appState, ui } from './state.js';
import { loadVideoPreview } from './timeline.js';
import { resetUI, showResults } from './ui.js';

// ========== UPLOAD & PREFS ==========

export async function handleFileSelect() {
  if (!ui.fileInput.files || !ui.fileInput.files[0]) return;
  
  const file = ui.fileInput.files[0];
  const formData = new FormData();
  formData.append('video', file);
  
  // Pegar token do localStorage
  const token = localStorage.getItem('access_token');
  if (!token) {
    alert('Você precisa fazer login primeiro!');
    window.location.href = '/login';
    return;
  }
  
  try {
    const response = await fetch('/api/videos/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (!response.ok) throw new Error(data.error || 'Erro desconhecido');
    
    appState.videoId = data.video.id;
    
    // Atualizar UI...
    ui.uploadView.classList.add('hidden');
    ui.previewView.classList.remove('hidden');
    
  } catch (error) {
    alert('Erro ao enviar arquivo: ' + error.message);
  }
}

// Nova função para chamar o backend e começar de verdade
export async function triggerProcessing() {
    if (!appState.sessionId) {
        alert("Erro: Sessão perdida. Faça o upload novamente.");
        return;
    }

    const preferences = getPreferences();
    
    // Se estiver em modo manual, adiciona os tempos
    if (appState.currentMode === 'manual') {
        // Pega valores dos inputs manuais se existirem, ou do estado
        const startInput = document.getElementById('manual-start-time');
        const endInput = document.getElementById('manual-end-time');
        if (startInput && endInput) {
             preferences.start_time = startInput.value;
             preferences.end_time = endInput.value;
        }
    }

    try {
        const response = await fetch(`/start-processing/${appState.sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(preferences)
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erro ao iniciar processamento");
        }

        // Se deu certo, mostra tela de loading e inicia polling
        ui.previewView.classList.add('hidden');
        ui.processingView.classList.remove('hidden');
        startProgressPolling(appState.sessionId);

    } catch (error) {
        alert("Falha ao iniciar: " + error.message);
        console.error(error);
    }
}

export async function cancelProcessing() {
    try {
        await fetch('/cancel-processing', { method: 'POST' });
        resetUI();
    } catch (e) {
        console.error(e);
        resetUI();
    }
}

// ... (Mantenha handleWatermarkUpload, removeWatermarkFile, getPreferences, savePreferences, loadSettings iguais) ...
// ... Abaixo coloco apenas as que não mudaram para referência, mas você pode manter as suas ...

export async function handleWatermarkUpload() {
    if (!ui.watermarkInput.files || !ui.watermarkInput.files[0]) return;
    const file = ui.watermarkInput.files[0];
    const formData = new FormData();
    formData.append('watermark', file);
    try {
      const response = await fetch('/upload-watermark', { method: 'POST', body: formData });
      const data = await response.json();
      if (data.success) {
        appState.watermarkPath = data.path;
        ui.watermarkPreview.src = URL.createObjectURL(file);
        document.getElementById('watermark-preview-container').classList.remove('hidden');
      }
    } catch (error) { console.error(error); }
}
  
export function removeWatermarkFile() {
    appState.watermarkPath = '';
    document.getElementById('watermark-preview-container').classList.add('hidden');
    ui.watermarkInput.value = '';
}

export function getPreferences() {
    const getVal = (id, isInt = false, isFloat = false) => {
      const el = document.getElementById(id);
      if (!el) return null;
      if (isInt) return parseInt(el.value);
      if (isFloat) return parseFloat(el.value);
      return el.value;
    };
    const getChecked = (id) => {
      const el = document.getElementById(id);
      return el ? el.checked : false;
    };
  
    return {
      subtitle_font: getVal('subtitle-font') || 'Courier-New-Bold',
      subtitle_size: getVal('subtitle-size', true) || 70,
      with_subtitles: getChecked('with-subtitles'),
      video_speed: getVal('video-speed', false, true) || 1.0,
      num_clips: getVal('num-clips', true) || 3,
      min_duration: 30,
      max_duration: 120,
      whisper_model: getVal('whisper-model') || 'base',
      fast_mode: false,
      watermark_path: appState.watermarkPath
    };
}

export async function savePreferences(scope) {
    const prefs = getPreferences();
    if (scope === 'all') {
      try {
        await fetch('/save-preferences', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(prefs)
        });
        alert('✅ Configurações salvas!');
      } catch { alert('❌ Erro ao salvar.'); }
    } else {
      alert('✅ Aplicado para este vídeo!');
    }
}

export async function loadSettings() {
    const setVal = (id, value) => { const el = document.getElementById(id); if (el) el.value = value; };
    const setChecked = (id, value) => { const el = document.getElementById(id); if (el) el.checked = value; };
    try {
      const response = await fetch('/get-preferences');
      const prefs = await response.json();
      setVal('subtitle-size', prefs.subtitle_size || 70);
      setVal('num-clips', prefs.num_clips || 3);
      setVal('whisper-model', prefs.whisper_model || 'base');
      setVal('video-speed', prefs.video_speed || 1.0);
      setVal('subtitle-font', prefs.subtitle_font || 'Courier-New-Bold');
      setChecked('with-subtitles', prefs.with_subtitles !== false);
    } catch (error) { console.error(error); }
}

export function startProgressPolling(sessionId) {
    let logUpdateCount = 0;
    
    appState.progressInterval = setInterval(async () => {
      try {
        const response = await fetch('/status/' + sessionId);
        const data = await response.json();
        
        if (data.progress !== undefined) {
          ui.progressFill.style.width = data.progress + '%';
          ui.progressPercent.textContent = Math.round(data.progress) + '%';
          ui.statusText.textContent = data.stage || 'Processando...';
        }
        
        if (data.logs && data.logs.length > logUpdateCount) {
          const newLogs = data.logs.slice(logUpdateCount);
          newLogs.forEach(log => {
            const entry = document.createElement('div');
            entry.className = 'flex gap-2 text-xs';
            entry.innerHTML = `<span class="text-primary font-bold">[${log.time}]</span> <span>${log.message}</span>`;
            ui.logContainer.appendChild(entry);
          });
          logUpdateCount = data.logs.length;
          ui.logContainer.scrollTop = ui.logContainer.scrollHeight;
        }
        
        if (data.done) {
          clearInterval(appState.progressInterval);
          if (data.error) {
            alert('❌ Erro: ' + data.error);
            resetUI();
          } else if (data.result && data.result.files && data.result.files.length > 0) {
            showResults(data.result);
          } else {
            alert('⚠️ Nenhum clipe gerado.');
            resetUI();
          }
        }
      } catch (error) {
        // Ignora erros de rede momentâneos
      }
    }, 1000);
}