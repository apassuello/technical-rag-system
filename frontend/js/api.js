// ---------------------------------------------------------------------------
// api.js -- API client (always hits the real backend served by serve.py)
// ---------------------------------------------------------------------------

import { AppState } from './state.js';

const API_BASE = '/api/v1/';

async function dispatch(endpoint, payload, method = 'POST') {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (method !== 'GET') {
      options.body = JSON.stringify(payload);
    }

    const res = await fetch(API_BASE + endpoint, options);
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`${res.status}: ${detail}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API error (${endpoint}):`, err.message);
    AppState.set('apiError', err.message);
    return null;
  }
}

async function submitQuery(text, strategy) {
  AppState.set('isLoading', true);
  AppState.set('apiError', null);
  try {
    const result = await dispatch('query', { query: text, strategy });
    AppState.set('queryResult', result);
    return result;
  } finally {
    AppState.set('isLoading', false);
  }
}

async function compareConfigs(query) {
  AppState.set('isLoading', true);
  AppState.set('apiError', null);
  try {
    const result = await dispatch('compare', { query });
    AppState.set('compareResults', result);
    return result;
  } finally {
    AppState.set('isLoading', false);
  }
}

async function checkConnection() {
  try {
    const res = await fetch(API_BASE + 'status', { method: 'GET' });
    const ok = res.ok;
    AppState.set('connectionStatus', ok ? 'connected' : 'disconnected');
    return ok;
  } catch {
    AppState.set('connectionStatus', 'disconnected');
    return false;
  }
}

async function fetchStats() {
  return dispatch('stats', null, 'GET');
}

async function fetchCorpus() {
  return dispatch('corpus', null, 'GET');
}

async function fetchComponents() {
  return dispatch('components', null, 'GET');
}

async function fetchConfigs() {
  return dispatch('configs', null, 'GET');
}

async function fetchServices() {
  return dispatch('services', null, 'GET');
}

async function fetchTrainingMetrics() {
  return dispatch('metrics/training', null, 'GET');
}

async function activateConfig(configName) {
  return dispatch('config/activate', { config_name: configName });
}

async function startService(name) {
  return dispatch('services/' + name + '/start', {});
}

async function uploadDocument(file) {
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch(API_BASE + 'documents/upload', {
      method: 'POST',
      body: form,
    });
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  } catch (err) {
    console.error('Upload error:', err.message);
    AppState.set('apiError', err.message);
    return null;
  }
}

async function indexCorpus() {
  return dispatch('corpus/index', {});
}

async function fetchWithFallback(endpoint, fallbackData) {
  const result = await dispatch(endpoint, null, 'GET');
  return result ?? fallbackData;
}

export {
  submitQuery,
  compareConfigs,
  checkConnection,
  fetchStats,
  fetchCorpus,
  fetchComponents,
  fetchConfigs,
  fetchServices,
  fetchTrainingMetrics,
  activateConfig,
  startService,
  uploadDocument,
  indexCorpus,
  fetchWithFallback,
};
