// ---------------------------------------------------------------------------
// state.js -- Observable state store + hash router for the SPA
// ---------------------------------------------------------------------------

const AppState = (() => {
  const _state = {
    activePage: 'home',
    isLoading: false,
    currentQuery: '',
    currentStrategy: 'balanced',
    queryResult: null,
    selectedDocument: null,
    selectedConfig: null,
    compareResults: null,
    selectedTrainingQuery: null,
    connectionStatus: 'disconnected',
    apiError: null,
  };

  /** @type {Map<string, Set<Function>>} */
  const _listeners = new Map();

  function get(key) {
    return _state[key];
  }

  function set(key, value) {
    _state[key] = value;
    const subs = _listeners.get(key);
    if (subs) {
      subs.forEach((cb) => cb(value));
    }
  }

  function on(key, callback) {
    if (!_listeners.has(key)) {
      _listeners.set(key, new Set());
    }
    _listeners.get(key).add(callback);
    return () => off(key, callback);
  }

  function off(key, callback) {
    const subs = _listeners.get(key);
    if (subs) {
      subs.delete(callback);
    }
  }

  return { get, set, on, off };
})();

// ---------------------------------------------------------------------------
// Hash Router
// ---------------------------------------------------------------------------

const VALID_PAGES = ['home', 'query', 'corpus', 'architecture', 'performance', 'setup'];

function parseHash() {
  const raw = location.hash.replace(/^#/, '');
  return VALID_PAGES.includes(raw) ? raw : 'home';
}

function navigateTo(page) {
  location.hash = '#' + page;
}

function applyPageView(page) {
  // Toggle page sections
  VALID_PAGES.forEach((name) => {
    const section = document.getElementById('page-' + name);
    if (section) {
      section.classList.toggle('active', name === page);
    }
  });

  // Toggle nav tabs
  document.querySelectorAll('.nav-tab[data-page]').forEach((tab) => {
    tab.classList.toggle('active', tab.dataset.page === page);
  });
}

// React to activePage changes
AppState.on('activePage', applyPageView);

// Hash-change handler
function onHashChange() {
  AppState.set('activePage', parseHash());
}

window.addEventListener('hashchange', onHashChange);

// Initial route on load
document.addEventListener('DOMContentLoaded', () => {
  onHashChange();
});

// If the DOM is already interactive/complete, also fire immediately so that
// scripts loaded with type="module" (deferred by default) pick up the route.
if (document.readyState !== 'loading') {
  onHashChange();
}

export { AppState, navigateTo };
