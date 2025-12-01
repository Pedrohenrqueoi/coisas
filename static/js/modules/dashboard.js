// static/js/modules/dashboard.js

import { ui } from './state.js';

export async function loadHistory() {
  if (!ui.historyList) return;
  try {
    const response = await fetch('/history');
    const history = await response.json();
    
    if (!history || history.length === 0) {
      ui.historyList.innerHTML = `
        <div class="p-16 text-center">
          <span class="material-symbols-outlined text-5xl text-text-secondary-dark mb-4 block">movie_off</span>
          <h3 class="text-lg font-semibold text-text-primary-dark mb-2">Nenhum processamento ainda</h3>
          <p class="text-text-secondary-dark">Comece processando um vídeo!</p>
        </div>
      `;
      return;
    }
    
    ui.historyList.innerHTML = '';
    history.forEach(item => {
      const date = new Date(item.date);
      const div = document.createElement('div');
      div.className = 'p-6 hover:bg-white/5 transition-colors border-b border-border-dark last:border-0';
      
      let clipsHtml = '';
      
      // NOVA ESTRUTURA PARA CADA CLIPE NO HISTÓRICO
      item.clips.forEach(clip => {
        const fileName = clip.file;
        const socialFile = fileName.replace('.mp4', '_social.txt');
        const metricsFile = fileName.replace('.mp4', '_metrics.txt');
        
        clipsHtml += `
          <div class="bg-black/30 p-3 rounded-lg border border-border-dark flex flex-col sm:flex-row gap-4 items-center">
             <div class="w-full sm:w-32 aspect-video bg-black rounded overflow-hidden flex-shrink-0">
                <video src="/done/${fileName}" class="w-full h-full object-cover" preload="metadata"></video>
             </div>
             
             <div class="flex-1 w-full flex flex-col gap-2">
                <p class="text-white font-bold text-sm truncate">${fileName}</p>
                <div class="flex gap-2 flex-wrap">
                   <a href="/done/${fileName}" download class="flex-1 sm:flex-none flex items-center justify-center gap-1 px-3 py-1.5 bg-primary/20 hover:bg-primary/30 text-primary text-xs font-bold rounded transition-colors">
                      <span class="material-symbols-outlined text-sm">download</span> Vídeo
                   </a>
                   <a href="/done/${socialFile}" download class="flex-1 sm:flex-none flex items-center justify-center gap-1 px-3 py-1.5 bg-secondary/10 hover:bg-secondary/20 text-secondary text-xs font-bold rounded transition-colors">
                      <span class="material-symbols-outlined text-sm">description</span> Post
                   </a>
                   <a href="/done/${metricsFile}" download class="flex-1 sm:flex-none flex items-center justify-center gap-1 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-text-secondary-dark text-xs font-bold rounded transition-colors">
                      <span class="material-symbols-outlined text-sm">analytics</span> IA
                   </a>
                </div>
             </div>
          </div>
        `;
      });

      div.innerHTML = `
        <div class="flex flex-col gap-4">
          <div class="flex justify-between items-start flex-wrap gap-4 mb-2">
            <div>
              <p class="text-lg font-bold text-white">${item.video_name}</p>
              <p class="text-xs text-text-secondary-dark capitalize">${date.toLocaleString('pt-BR')}</p>
            </div>
            <div class="flex gap-2 flex-wrap">
              <span class="bg-border-dark text-text-secondary-dark text-xs px-2.5 py-1 rounded-full flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">movie</span>
                ${item.clips_count} clips
              </span>
              <span class="bg-secondary/20 text-secondary text-xs px-2.5 py-1 rounded-full flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">trending_up</span>
                Score: ${Math.round(item.avg_score)}
              </span>
            </div>
          </div>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
            ${clipsHtml}
          </div>
        </div>
      `;
      ui.historyList.appendChild(div);
    });
    
  } catch (error) {
    console.error('Erro ao carregar histórico:', error);
  }
}

export async function loadDashboard() {
  if (!ui.totalClips) return;
  try {
    const response = await fetch('/analytics');
    const data = await response.json();
    
    ui.totalClips.textContent = data.total_clips || 0;
    ui.avgScore.textContent = Math.round(data.avg_score || 0);
    ui.totalSessions.textContent = data.sessions?.length || 0;
    ui.avgDurationStat.textContent = Math.round(data.avg_duration || 0) + 's';
    
    renderChart('keywordsChartInstance', 'keywordsChart', 'bar', getKeywordsChartConfig(data));
    renderChart('narrativeChartInstance', 'narrativeChart', 'pie', getNarrativeChartConfig(data));
    renderChart('sentimentChartInstance', 'sentimentChart', 'doughnut', getSentimentChartConfig(data));
    
  } catch (error) {
    console.error('Erro ao carregar dashboard:', error);
  }
}

function renderChart(instanceName, canvasId, type, config) {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return;
  
  if (window[instanceName]) {
    window[instanceName].destroy();
  }
  if (!config) {
    return;
  }
  window[instanceName] = new Chart(ctx, { type, ...config });
}

function getKeywordsChartConfig(data) {
  const keywords = data.keywords || [];
  const keywordCount = {};
  keywords.forEach(word => { keywordCount[word] = (keywordCount[word] || 0) + 1; });
  const sortedKeywords = Object.entries(keywordCount).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const labels = sortedKeywords.map(k => k[0]);
  const values = sortedKeywords.map(k => k[1]);
  if (labels.length === 0) return null;
  return {
    data: { 
      labels, 
      datasets: [{ 
        label: 'Frequência', 
        data: values, 
        backgroundColor: 'rgba(58, 125, 255, 0.8)', 
        borderColor: '#3A7DFF', 
        borderWidth: 2 
      }] 
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false, 
      plugins: { 
        legend: { display: false }, 
        title: { display: false }
      }, 
      scales: { 
        y: { 
          beginAtZero: true, 
          ticks: { color: 'white' }, 
          grid: { color: 'rgba(255,255,255,0.1)' } 
        }, 
        x: { 
          ticks: { color: 'white' }, 
          grid: { display: false } 
        } 
      } 
    }
  };
}

function getNarrativeChartConfig(data) {
  const narratives = data.narratives || {INTRODUCAO: 0, CONTEXTO: 0, CLIMAX: 0};
  const labels = Object.keys(narratives);
  const values = Object.values(narratives);
  if (values.reduce((a, b) => a + b, 0) === 0) return null;
  return {
    data: { 
      labels: labels.map(l => ({'INTRODUCAO': 'Introdução', 'CONTEXTO': 'Contexto', 'CLIMAX': 'Clímax'}[l] || l)), 
      datasets: [{ 
        data: values, 
        backgroundColor: ['#3A7DFF', '#00DDA3', '#FFA500'] 
      }] 
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false, 
      plugins: { 
        legend: { 
          position: 'bottom', 
          labels: { color: 'white', font: { size: 12 } } 
        }
      } 
    }
  };
}

function getSentimentChartConfig(data) {
  const sentiments = data.sentiments || {};
  const labels = Object.keys(sentiments);
  const values = Object.values(sentiments);
  if (values.reduce((a, b) => a + b, 0) === 0) return null;
  const sentimentColors = { 
    'URGENTE': '#FF6B6B', 
    'ALERTA': '#FFA500', 
    'SERIO': '#4ECDC4', 
    'POSITIVO': '#00DDA3', 
    'NEUTRO': '#A0A0A0' 
  };
  const colors = labels.map(label => sentimentColors[label] || '#A0A0A0');
  return {
    data: { 
      labels, 
      datasets: [{ 
        data: values, 
        backgroundColor: colors, 
        borderWidth: 2, 
        borderColor: '#1e1e1e' 
      }] 
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false, 
      plugins: { 
        legend: { 
          position: 'bottom', 
          labels: { color: 'white', font: { size: 12 } } 
        }
      } 
    }
  };
}