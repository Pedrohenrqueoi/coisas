import { appState, ui } from './state.js';
import { drawTimelineFrames } from './ui.js';

export async function loadVideoPreview() {
  try {
    const response = await fetch(`/preview/${appState.sessionId}`);
    const data = await response.json();
    
    if (data.error) {
      console.error('Erro ao carregar preview:', data.error);
      return;
    }
    
    appState.videoInfo = data;
    ui.videoPlayer.src = `/video/${data.filename}`;
    
    appState.timelineEndTime = data.duration;
    updateTimelineDisplay();
    updateManualTimeInputs();
    drawTimelineFrames();
    
    console.log('✓ Preview carregado:', data);
    
  } catch (error) {
    console.error('Erro ao carregar preview:', error);
  }
}

export function selectMode(mode) {
  appState.currentMode = mode;
  
  ui.modeAutoBtn.classList.remove('active');
  ui.modeManualBtn.classList.remove('active');
  
  if (mode === 'auto') {
    ui.modeAutoBtn.classList.add('active');
    ui.timelineSection.classList.add('hidden');
  } else {
    ui.modeManualBtn.classList.add('active');
    ui.timelineSection.classList.remove('hidden');
  }
}

export function initializeTimeline() {
  if (!ui.markerStart) return; 
  
  let isDragging = false;
  let currentMarker = null;
  
  const startDrag = (e, marker) => {
    isDragging = true;
    currentMarker = marker;
    e.preventDefault();
  };
  
  const endDrag = () => {
    isDragging = false;
    currentMarker = null;
  };
  
  const onDrag = (e) => {
    if (!isDragging || !currentMarker || !appState.videoInfo) return;
  
    const wrapper = ui.timelineCanvas.parentElement;
    const rect = wrapper.getBoundingClientRect();
    
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const x = clientX - rect.left;
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
    
    if (currentMarker === 'start') {
      const endPercent = parseFloat(ui.markerEnd.style.right) || 0;
      if (percent < (100 - endPercent)) {
        ui.markerStart.style.left = percent + '%';
        appState.timelineStartTime = (percent / 100) * appState.videoInfo.duration;
      }
    } else if (currentMarker === 'end') {
      const startPercent = parseFloat(ui.markerStart.style.left) || 0;
      if (percent > startPercent) {
        ui.markerEnd.style.right = (100 - percent) + '%';
        appState.timelineEndTime = (percent / 100) * appState.videoInfo.duration;
      }
    }
    updateTimelineDisplay();
    updateManualTimeInputs();
  };
  
  ui.markerStart.addEventListener('mousedown', (e) => startDrag(e, 'start'));
  ui.markerEnd.addEventListener('mousedown', (e) => startDrag(e, 'end'));
  ui.markerStart.addEventListener('touchstart', (e) => startDrag(e, 'start'));
  ui.markerEnd.addEventListener('touchstart', (e) => startDrag(e, 'end'));
  
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('touchmove', onDrag);
  document.addEventListener('mouseup', endDrag);
  document.addEventListener('touchend', endDrag);
}

export function setMarkerFromVideo(type) {
  const currentTime = ui.videoPlayer.currentTime;
  const percent = (currentTime / appState.videoInfo.duration) * 100;
  
  if (type === 'start') {
    ui.markerStart.style.left = percent + '%';
    appState.timelineStartTime = currentTime;
  } else {
    ui.markerEnd.style.right = (100 - percent) + '%';
    appState.timelineEndTime = currentTime;
  }
  
  updateTimelineDisplay();
  updateManualTimeInputs();
}

export function applyManualTimes() {
  const startSeconds = parseTimeString(ui.manualStartTimeInput.value);
  const endSeconds = parseTimeString(ui.manualEndTimeInput.value);
  
  if (startSeconds === null || endSeconds === null) {
    alert('❌ Formato de tempo inválido. Use HH:MM:SS ou MM:SS\n\nExemplos:\n• 00:01:30\n• 01:30');
    return;
  }
  if (startSeconds >= endSeconds) {
    alert('❌ O tempo de início deve ser MENOR que o tempo de fim');
    return;
  }
  if (endSeconds > appState.videoInfo.duration) {
    alert(`❌ O tempo de fim (${formatTime(endSeconds)}) excede a duração do vídeo (${formatTime(appState.videoInfo.duration)})`);
    return;
  }
  
  appState.timelineStartTime = startSeconds;
  appState.timelineEndTime = endSeconds;
  
  const startPercent = (startSeconds / appState.videoInfo.duration) * 100;
  const endPercent = (endSeconds / appState.videoInfo.duration) * 100;
  
  ui.markerStart.style.left = startPercent + '%';
  ui.markerEnd.style.right = (100 - endPercent) + '%';
  
  updateTimelineDisplay();
  ui.videoPlayer.currentTime = startSeconds;
  
  alert(`✅ Tempos aplicados!\n\nInício: ${formatTime(startSeconds)}\nFim: ${formatTime(endSeconds)}`);
}

export function parseTimeString(timeStr) {
  if (!timeStr || timeStr.trim() === '') return null;
  const parts = timeStr.split(':').map(p => parseInt(p));
  if (parts.some(isNaN)) return null;
  
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 1) return parts[0];
  return null;
}

export function updateManualTimeInputs() {
  if (ui.manualStartTimeInput && ui.manualEndTimeInput) {
    ui.manualStartTimeInput.value = formatTime(appState.timelineStartTime);
    ui.manualEndTimeInput.value = formatTime(appState.timelineEndTime);
  }
}

export function resetTimeline() {
  ui.markerStart.style.left = '0%';
  ui.markerEnd.style.right = '0%';
  appState.timelineStartTime = 0;
  appState.timelineEndTime = appState.videoInfo.duration;
  updateTimelineDisplay();
  updateManualTimeInputs();
}

export function updateTimelineDisplay() {
  if (!appState.videoInfo) return;
  
  const startPercent = (appState.timelineStartTime / appState.videoInfo.duration) * 100;
  const endPercent = (appState.timelineEndTime / appState.videoInfo.duration) * 100;
  
  ui.timelineSelection.style.left = startPercent + '%';
  ui.timelineSelection.style.width = (endPercent - startPercent) + '%';
  
  ui.timeStartDisplay.textContent = formatTime(appState.timelineStartTime);
  ui.timeEndDisplay.textContent = formatTime(appState.timelineEndTime);
  ui.timeDurationDisplay.textContent = formatTime(appState.timelineEndTime - appState.timelineStartTime);
}

export function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
