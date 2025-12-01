// static/js/modules/ui.js

import { appState, ui } from './state.js';
import { loadDashboard, loadHistory } from './dashboard.js';
import { formatTime } from './timeline.js';

export function switchTab(tabName) {
  document.querySelectorAll('.tab-content, #processing-view, #results-view').forEach(content => {
    content.classList.remove('active');
    content.classList.add('hidden');
  });
  
  const activeContent = document.getElementById('tab-' + tabName);
  if (activeContent) {
    activeContent.classList.remove('hidden');
    activeContent.classList.add('active');
  }
  
  if (tabName === 'dashboard') loadDashboard();
  else if (tabName === 'history') loadHistory();
}

export function showResults(result) {
  ui.processingView.classList.add('hidden');
  ui.resultsView.classList.remove('hidden');
  ui.resultsList.innerHTML = '';
  
  result.files.forEach((file, index) => {
    const card = document.createElement('div');
    card.className = 'bg-card-dark rounded-lg border border-border-dark p-4';
    
    // CORREÇÃO DOS LINKS ABAIXO
    card.innerHTML = `
      <div class="aspect-video bg-black rounded-lg mb-4 overflow-hidden">
        <video class="w-full h-full" controls preload="metadata">
          <source src="/done/${file}" type="video/mp4">
        </video>
      </div>
      <p class="text-white text-lg font-bold mb-3">🎬 Clipe ${index + 1}</p>
      <div class="flex flex-col gap-2">
        <a href="/done/${file}" download class="flex items-center justify-center gap-2 px-3 py-2 bg-primary/20 text-white text-sm font-bold rounded-lg hover:bg-primary/30 transition-colors">
          <span class="material-symbols-outlined text-base">download</span>
          <span>Vídeo</span>
        </a>
        <a href="/done/${file.replace('.mp4','_social.txt')}" download class="flex items-center justify-center gap-2 px-3 py-2 bg-secondary/10 text-secondary text-sm font-bold rounded-lg hover:bg-secondary/20 transition-colors">
          <span class="material-symbols-outlined text-base">article</span>
          <span>Post & Legenda</span>
        </a>
        <a href="/done/${file.replace('.mp4','_metrics.txt')}" download class="flex items-center justify-center gap-2 px-3 py-2 bg-white/5 text-text-secondary-dark text-sm font-bold rounded-lg hover:bg-white/10 transition-colors">
          <span class="material-symbols-outlined text-base">insights</span>
          <span>Relatório IA</span>
        </a>
      </div>
    `;
    ui.resultsList.appendChild(card);
  });
  
  ui.downloadAllBtn.classList.remove('hidden');
  ui.downloadAllBtn.onclick = () => {
    window.location.href = '/download-all/' + result.session_id;
  };
  
  if (result.analytics) {
    ui.analyticsSection.classList.remove('hidden');
    ui.statClips.textContent = result.analytics.total_clips;
    ui.statScore.textContent = Math.round(result.analytics.avg_score);
    ui.statDuration.textContent = Math.round(result.analytics.total_duration) + 's';
    ui.statSentiment.textContent = result.analytics.sentiment.sentiment;
    ui.statTime.textContent = Math.round(result.analytics.processing_time || 0) + 's';
  }
  
  loadHistory();
  loadDashboard();
}

export function resetUI() {
  ui.uploadView.classList.remove('hidden');
  ui.previewView.classList.add('hidden');
  ui.processingView.classList.add('hidden');
  ui.resultsView.classList.add('hidden');
  ui.fileInput.value = '';
  
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.remove('bg-primary/20', 'text-primary');
    tab.classList.add('text-text-secondary-dark');
    tab.classList.remove('active-nav');
  });
  
  const uploadTab = document.querySelector('.nav-tab[data-tab="upload"]');
  if (uploadTab) {
    uploadTab.classList.add('active-nav'); 
  }
  
  switchTab('upload');
  
  appState.sessionId = null;
  appState.videoInfo = null;
  appState.currentMode = 'auto';
  appState.timelineStartTime = 0;
  appState.timelineEndTime = 0;
  
  ui.logContainer.innerHTML = `
    <div class="log-entry">
      <span class="text-secondary">--:--:--</span>
      <span class="ml-2">Aguardando início...</span>
    </div>
  `;
}

export function drawTimelineFrames() {
  if (!ui.timelineCanvas) return;
  const ctx = ui.timelineCanvas.getContext('2d');
  ui.timelineCanvas.width = ui.timelineCanvas.offsetWidth;
  ui.timelineCanvas.height = ui.timelineCanvas.offsetHeight;
  
  const gradient = ctx.createLinearGradient(0, 0, ui.timelineCanvas.width, 0);
  gradient.addColorStop(0, '#3A7DFF');
  gradient.addColorStop(0.5, '#00DDA3');
  gradient.addColorStop(1, '#3A7DFF');
  
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, ui.timelineCanvas.width, ui.timelineCanvas.height);
  
  ctx.fillStyle = 'rgba(255,255,255,0.2)';
  const numMarkers = 10;
  for (let i = 0; i <= numMarkers; i++) {
    const x = (ui.timelineCanvas.width / numMarkers) * i;
    ctx.fillRect(x, 0, 1, ui.timelineCanvas.height);
  }
}