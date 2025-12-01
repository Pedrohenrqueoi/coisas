// static/js/modules/state.js

export const appState = {
  sessionId: null,
  progressInterval: null,
  currentMode: 'auto',
  videoInfo: null,
  timelineStartTime: 0,
  timelineEndTime: 0,
  uploadedFileName: null,
  watermarkPath: ''
};

export const ui = {};

export function mapUI() {
  // Navegação Sidebar
  ui.navTabs = document.querySelectorAll('.nav-tab');
  
  // Upload & Drop Area
  ui.dropArea = document.getElementById('drop-area');
  ui.fileInput = document.getElementById('file-input');
  // O botão de upload está dentro do drop area ou é um elemento separado
  // No novo HTML, ele tem a classe .upload-btn
  ui.uploadBtn = document.querySelector('.upload-btn'); 
  
  // Views (Telas)
  ui.uploadView = document.getElementById('upload-view'); // A div inicial de upload
  ui.previewView = document.getElementById('preview-view'); // A div de preview
  ui.processingView = document.getElementById('processing-view'); // O overlay de processamento
  ui.resultsView = document.getElementById('results-view'); // O overlay de resultados
  ui.settingsCard = document.getElementById('settings-card'); // Card lateral de configs

  // Video Player
  ui.videoPlayer = document.getElementById('video-preview');
  
  // Botões de Modo (Auto/Manual) - Agora são radio inputs
  const modeRadios = document.querySelectorAll('input[name="mode"]');
  ui.modeAutoBtn = modeRadios[0]?.parentElement; // Label do Auto
  ui.modeManualBtn = modeRadios[1]?.parentElement; // Label do Manual
  
  // Timeline Manual
  ui.timelineSection = document.getElementById('timeline-section');
  ui.timelineCanvas = document.getElementById('timeline-canvas');
  ui.timelineSelection = document.getElementById('timeline-selection');
  ui.markerStart = document.getElementById('marker-start');
  ui.markerEnd = document.getElementById('marker-end');
  ui.manualStartTimeInput = document.getElementById('manual-start-time');
  ui.manualEndTimeInput = document.getElementById('manual-end-time');
  ui.timeStartDisplay = document.getElementById('time-start'); // Invisível, mas usado na lógica
  ui.timeEndDisplay = document.getElementById('time-end');
  ui.timeDurationDisplay = document.getElementById('time-duration');

  // Watermark
  ui.watermarkUpload = document.getElementById('watermark-upload');
  ui.watermarkInput = document.getElementById('watermark-input');
  ui.watermarkPreview = document.getElementById('watermark-preview');
  ui.removeWatermarkBtn = document.getElementById('remove-watermark');

  // Processing & Logs
  ui.progressFill = document.getElementById('progress-fill');
  ui.progressPercent = document.getElementById('progress-percent');
  ui.statusText = document.getElementById('status-text');
  ui.logContainer = document.getElementById('log-container');

  // Results & Analytics
  ui.resultsList = document.getElementById('results-list');
  ui.downloadAllBtn = document.getElementById('download-all-btn');
  ui.analyticsSection = document.getElementById('analytics-section');
  ui.statClips = document.getElementById('stat-clips');
  ui.statScore = document.getElementById('stat-score');
  ui.statDuration = document.getElementById('stat-duration');
  ui.statSentiment = document.getElementById('stat-sentiment');
  ui.statTime = document.getElementById('stat-time');

  // Dashboard & History Containers (Para saber onde injetar)
  ui.historyList = document.getElementById('history-list');
  ui.totalClips = document.getElementById('total-clips');
  ui.avgScore = document.getElementById('avg-score');
  ui.totalSessions = document.getElementById('total-sessions');
  ui.avgDurationStat = document.getElementById('avg-duration-stat');

  console.log('✓ UI Mapeada (Elementos encontrados)');
}