/* ===================================================
   ARQUIVO: static/js/app.js (Main Controller)
   =================================================== */

import { appState, ui, mapUI } from './modules/state.js';
import { loadDashboard, loadHistory } from './modules/dashboard.js'; 
import { switchTab, resetUI } from './modules/ui.js';
import { 
  handleFileSelect, 
  handleWatermarkUpload, 
  removeWatermarkFile,
  savePreferences, 
  loadSettings, 
  triggerProcessing,
  cancelProcessing
} from './modules/api.js';
import { 
  initializeTimeline, 
  selectMode, 
  setMarkerFromVideo, 
  applyManualTimes, 
  resetTimeline
} from './modules/timeline.js';

document.addEventListener('DOMContentLoaded', () => {
  mapUI();
  initializeEventListeners();
  initializeSidebarNavigation();
  loadSettings();
  
  // --- CORREÇÃO AQUI ---
  // Força a aba de upload a abrir assim que o site carrega
  switchTab('upload'); 
  
  console.log('✓ VideoAI pronto');
});

function initializeEventListeners() {
  if (ui.uploadBtn) ui.uploadBtn.addEventListener('click', () => ui.fileInput.click());
  if (ui.fileInput) ui.fileInput.addEventListener('change', handleFileSelect);
  
  if (ui.dropArea) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      ui.dropArea.addEventListener(eventName, (e) => e.preventDefault(), false);
    });
    // Adicione efeitos visuais de drag aqui se desejar
    ui.dropArea.addEventListener('drop', (e) => {
      e.preventDefault();
      const dt = e.dataTransfer;
      if (dt.files.length > 0) {
        ui.fileInput.files = dt.files;
        handleFileSelect();
      }
    });
  }
  
  if (ui.watermarkUpload) {
    ui.watermarkUpload.addEventListener('click', () => ui.watermarkInput.click());
    ui.watermarkInput.addEventListener('change', handleWatermarkUpload);
    if(ui.removeWatermarkBtn) ui.removeWatermarkBtn.addEventListener('click', removeWatermarkFile);
  }
  
  document.querySelectorAll('input[name="mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => selectMode(e.target.value));
  });
  
  initializeTimeline();
}

function initializeSidebarNavigation() {
  const navTabs = document.querySelectorAll('.nav-tab');
  
  navTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const tabName = tab.dataset.tab;
      
      // 1. Esconde as telas de overlay (Resultados/Processamento)
      const procView = document.getElementById('processing-view');
      const resView = document.getElementById('results-view');
      if(procView) procView.classList.add('hidden');
      if(resView) resView.classList.add('hidden');
      
      // 2. Atualiza classes da sidebar
      navTabs.forEach(t => {
          t.classList.remove('active-nav');
          t.classList.remove('bg-white/5'); 
      });
      tab.classList.add('active-nav');
      
      // 3. Troca o conteúdo principal
      switchTab(tabName);

      // 4. Carrega dados dinâmicos se necessário
      if (tabName === 'dashboard') {
          loadDashboard();
      } else if (tabName === 'history') {
          loadHistory();
      }
    });
  });
}

window.app = {
  savePreferences,
  selectMode,
  applyManualTimes,
  setMarkerFromVideo,
  resetTimeline,
  resetUI: async () => {
      // Se estiver processando, cancela. Se estiver no resultado, só volta.
      const procView = document.getElementById('processing-view');
      if (procView && !procView.classList.contains('hidden')) {
          await cancelProcessing();
      } else {
          resetUI();
      }
  },
  startProcessing: triggerProcessing
};