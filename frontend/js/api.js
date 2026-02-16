// ---------------------------------------------------------------------------
// api.js -- Dual-mode API client (demo mock / live backend)
// ---------------------------------------------------------------------------

import { AppState } from './state.js';
import { MOCK_DATA } from './data.js';

const API_BASE = 'http://localhost:8080/api/v1/';

function delay(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function mockLatency() {
  return delay(200 + Math.random() * 200);
}

function classifyQuery(text) {
  const lower = text.toLowerCase();
  if (lower.includes('calculate') || lower.includes('how many') || lower.includes('what is'))
    return 'agent';
  if (lower.includes('compare') || lower.includes('versus') || text.length > 100)
    return 'complex';
  return 'simple';
}

async function dispatch(endpoint, payload) {
  if (AppState.get('mode') === 'demo') {
    await mockLatency();
    if (endpoint === 'query') return MOCK_DATA.queryMocks[classifyQuery(payload.query)];
    if (endpoint === 'compare') return MOCK_DATA.configComparison;
    if (endpoint === 'status') return getStatus();
    return null;
  }

  try {
    const res = await fetch(API_BASE + endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.warn(`Live API failed (${endpoint}), falling back to demo data:`, err.message);
    await mockLatency();
    if (endpoint === 'query') return MOCK_DATA.queryMocks[classifyQuery(payload.query)];
    if (endpoint === 'compare') return MOCK_DATA.configComparison;
    return null;
  }
}

async function submitQuery(text, strategy) {
  AppState.set('isLoading', true);
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

function getStatus() {
  return {
    status: 'operational',
    mode: AppState.get('mode'),
    services: { gateway: true, retriever: true, generator: true, analyzer: true },
  };
}

export { submitQuery, compareConfigs, checkConnection, getStatus };
