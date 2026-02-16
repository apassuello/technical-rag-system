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
};

const renderedPages = new Set();

function renderPage(page) {
  // Destroy existing charts before switching
  destroyAllCharts();

  const renderer = PAGE_RENDERERS[page];
  if (renderer) {
    // Only re-render pages that need fresh state (query, performance)
    // or haven't been rendered yet
    const alwaysRerender = new Set(['query', 'performance']);
    if (!renderedPages.has(page) || alwaysRerender.has(page)) {
      renderer();
      renderedPages.add(page);
    }
  }
}

// ---------------------------------------------------------------------------
// Mode toggle
// ---------------------------------------------------------------------------

function initModeToggle() {
  const btn = document.getElementById('mode-btn');
  const indicator = document.querySelector('.mode-toggle__indicator');
  const label = document.querySelector('.mode-toggle__label');

  if (!btn) return;

  btn.addEventListener('click', () => {
    const current = AppState.get('mode');
    const next = current === 'demo' ? 'live' : 'demo';
    AppState.set('mode', next);
  });

  AppState.on('mode', (mode) => {
    if (label) label.textContent = mode.toUpperCase();
    if (btn) btn.textContent = mode === 'demo' ? 'Switch to Live' : 'Switch to Demo';

    if (mode === 'live') {
      checkConnection();
    } else if (indicator) {
      indicator.classList.remove('disconnected');
    }
  });

  AppState.on('connectionStatus', (status) => {
    if (indicator) {
      indicator.classList.toggle('disconnected', status !== 'connected');
    }
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
  initModeToggle();

  // Render the initial page
  const initialPage = AppState.get('activePage');
  renderPage(initialPage);
});
