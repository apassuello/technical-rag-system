// ---------------------------------------------------------------------------
// app.js -- Application initialization and event wiring
// ---------------------------------------------------------------------------

import { AppState, navigateTo } from './state.js';
import { checkConnection } from './api.js';
import { destroyAllCharts } from './charts.js';
import {
  renderHomePage,
  renderQueryPage,
  renderCorpusPage,
  renderArchitecturePage,
  renderPerformancePage,
  renderSetupPage,
} from './pages.js';

// ---------------------------------------------------------------------------
// Page render dispatcher
// ---------------------------------------------------------------------------

const PAGE_RENDERERS = {
  home: renderHomePage,
  query: renderQueryPage,
  corpus: renderCorpusPage,
  architecture: renderArchitecturePage,
  performance: renderPerformancePage,
  setup: renderSetupPage,
};

const renderedPages = new Set();

function renderPage(page) {
  // Destroy existing charts before switching
  destroyAllCharts();

  const renderer = PAGE_RENDERERS[page];
  if (renderer) {
    // Only re-render pages that need fresh state (query, performance)
    // or haven't been rendered yet
    const alwaysRerender = new Set(['query', 'performance', 'setup']);
    if (!renderedPages.has(page) || alwaysRerender.has(page)) {
      renderer();
      renderedPages.add(page);
    }
  }
}

// ---------------------------------------------------------------------------
// LLM settings panel
// ---------------------------------------------------------------------------

const CLOUD_PROVIDERS = new Set(['openai', 'anthropic', 'mistral', 'huggingface']);

const MODEL_DEFAULTS = {
  local: 'qwen2.5-1.5b-instruct',
  ollama: 'mistral:latest',
  openai: 'gpt-4o-mini',
  anthropic: 'claude-3-haiku-20240307',
  mistral: 'mistral-small-latest',
  huggingface: 'mistralai/Mistral-7B-Instruct-v0.2',
  mock: 'mock-model',
};

function initLLMSettings() {
  const providerEl = document.getElementById('llm-provider');
  const modelEl = document.getElementById('llm-model');
  const keyEl = document.getElementById('llm-key');
  const applyBtn = document.getElementById('llm-apply');
  const statusEl = document.getElementById('llm-status');

  if (!providerEl) return;

  // Toggle API key visibility based on provider
  function syncKeyVisibility() {
    const isCloud = CLOUD_PROVIDERS.has(providerEl.value);
    keyEl.style.display = isCloud ? '' : 'none';
  }

  providerEl.addEventListener('change', () => {
    modelEl.value = MODEL_DEFAULTS[providerEl.value] || '';
    syncKeyVisibility();
  });

  applyBtn.addEventListener('click', async () => {
    const body = { provider: providerEl.value, model: modelEl.value };
    if (keyEl.value) body.api_key = keyEl.value;

    statusEl.textContent = '...';
    statusEl.className = 'llm-status';

    try {
      const res = await fetch('/api/v1/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        statusEl.textContent = 'OK';
        statusEl.className = 'llm-status llm-status--ok';
      } else {
        const data = await res.json().catch(() => ({}));
        statusEl.textContent = 'ERR';
        statusEl.className = 'llm-status llm-status--err';
        console.error('Settings error:', data.detail || res.statusText);
      }
    } catch (e) {
      statusEl.textContent = 'ERR';
      statusEl.className = 'llm-status llm-status--err';
      console.error('Settings fetch failed:', e);
    }
  });

  // On boot: fetch current status and sync the UI
  fetchAndSyncStatus(providerEl, modelEl, statusEl, syncKeyVisibility);
}

async function fetchAndSyncStatus(providerEl, modelEl, statusEl, syncKeyVisibility) {
  try {
    const res = await fetch('/api/v1/status');
    if (!res.ok) return;
    const data = await res.json();

    if (data.llm) {
      providerEl.value = data.llm.provider || 'mock';
      modelEl.value = data.llm.model || '';
      syncKeyVisibility();
    }

    AppState.set('connectionStatus', 'connected');
    statusEl.textContent = 'OK';
    statusEl.className = 'llm-status llm-status--ok';
  } catch {
    AppState.set('connectionStatus', 'disconnected');
    statusEl.textContent = 'OFF';
    statusEl.className = 'llm-status llm-status--err';
  }
}

// ---------------------------------------------------------------------------
// Navigation wiring
// ---------------------------------------------------------------------------

function initNavigation() {
  // Wire nav tab clicks to hash navigation
  document.querySelectorAll('.nav-tab[data-page]').forEach((tab) => {
    tab.addEventListener('click', () => {
      navigateTo(tab.dataset.page);
    });
  });

  // Render page when active page changes
  AppState.on('activePage', (page) => {
    renderPage(page);
  });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initLLMSettings();

  // Render the initial page
  const initialPage = AppState.get('activePage');
  renderPage(initialPage);
});
