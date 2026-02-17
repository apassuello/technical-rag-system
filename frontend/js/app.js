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

function initLLMSettings() {
  const labelEl = document.getElementById('llm-label');
  const dotEl = document.getElementById('llm-dot');
  if (!labelEl) return;

  fetch('/api/v1/status').then(r => r.json()).then(data => {
    if (data.llm) {
      labelEl.textContent = data.llm.provider + '/' + data.llm.model;
    }
    AppState.set('connectionStatus', 'connected');
    dotEl.classList.add('llm-compact__dot--ok');
  }).catch(() => {
    AppState.set('connectionStatus', 'disconnected');
    dotEl.classList.add('llm-compact__dot--err');
  });
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
  initOfflineDetection();

  // Render the initial page
  const initialPage = AppState.get('activePage');
  renderPage(initialPage);
});

// ---------------------------------------------------------------------------
// Offline detection and reconnection
// ---------------------------------------------------------------------------

async function initOfflineDetection() {
  const connected = await checkConnection();
  AppState.set('offline', !connected);

  if (!connected) {
    showOfflineNotice();
    startReconnectionPolling();
  }
}

let _reconnectTimer = null;

function startReconnectionPolling() {
  if (_reconnectTimer) return;
  _reconnectTimer = setInterval(async () => {
    const connected = await checkConnection();
    if (connected) {
      clearInterval(_reconnectTimer);
      _reconnectTimer = null;
      AppState.set('offline', false);
      hideOfflineNotice();
      // Re-render current page to pick up live data
      const page = AppState.get('activePage');
      renderedPages.delete(page);
      renderPage(page);
    }
  }, 30000);
}

function showOfflineNotice() {
  let notice = document.getElementById('offline-notice');
  if (notice) return;
  notice = document.createElement('div');
  notice.id = 'offline-notice';
  notice.className = 'offline-notice';
  notice.textContent = 'Offline — showing cached data';
  const main = document.querySelector('main');
  if (main) main.insertBefore(notice, main.firstChild);
}

function hideOfflineNotice() {
  const notice = document.getElementById('offline-notice');
  if (notice) notice.remove();
}
