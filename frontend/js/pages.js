// ---------------------------------------------------------------------------
// pages.js -- Page-level composition (wires components + charts + data)
// ---------------------------------------------------------------------------

import { AppState, navigateTo } from './state.js';
import { MOCK_DATA } from './data.js';
import { submitQuery } from './api.js';
import {
  renderConfidenceGauge,
  renderBadge,
  renderMetricCard,
  renderDataTable,
  renderSourceCard,
  renderReasoningStep,
  renderTreeNode,
  renderConfigBlock,
  renderPipelineTiming,
  renderCostBreakdown,
} from './components.js';
import {
  createRadarChart,
  createDoughnutChart,
  createHorizontalBarChart,
  createGroupedBarChart,
  createStackedBarChart,
  createCostComparisonChart,
  destroyAllCharts,
  getOrCreateCanvas,
} from './charts.js';


// ===========================================================================
// HOME PAGE
// ===========================================================================

export function renderHomePage() {
  const container = document.getElementById('home-content');
  if (!container) return;
  container.innerHTML = '';

  container.appendChild(buildHero());
  container.appendChild(buildCapabilityGrid());
  container.appendChild(buildStatsBar());
  container.appendChild(buildTechStack());
  container.appendChild(buildCTA());
}

// -- Hero -------------------------------------------------------------------

function buildHero() {
  const hero = document.createElement('section');
  hero.className = 'hero';

  const title = document.createElement('h1');
  title.className = 'hero__title';
  title.textContent = 'Technical Documentation RAG';

  const subtitle = document.createElement('h2');
  subtitle.className = 'hero__subtitle';
  subtitle.textContent = 'RISC-V Knowledge System';

  const desc = document.createElement('p');
  desc.className = 'hero__desc';
  desc.textContent =
    'Multi-model retrieval-augmented generation system for technical documentation. ' +
    'Combines semantic search, BM25 sparse retrieval, neural reranking, and intelligent ' +
    'query routing to deliver precise answers from a 73-document RISC-V corpus.';

  hero.appendChild(title);
  hero.appendChild(subtitle);
  hero.appendChild(desc);
  return hero;
}

// -- Capability Cards -------------------------------------------------------

const CAPABILITIES = [
  {
    epic: 'EPIC 1',
    badgeVariant: 'accent',
    title: 'Multi-Model Intelligence',
    metrics: [
      '98% classification accuracy',
      '40% cost reduction via routing',
      '5-view query analysis',
    ],
    description:
      'ML-trained query analyzer routes to optimal model based on complexity. ' +
      'Five analytical views score each query across technical, linguistic, semantic, ' +
      'computational, and task dimensions.',
  },
  {
    epic: 'EPIC 2',
    badgeVariant: 'info',
    title: 'Advanced Retrieval',
    metrics: [
      'Hybrid search (FAISS + BM25)',
      '4 fusion strategies',
      'Neural reranking',
    ],
    description:
      'Dense and sparse retrieval with configurable fusion. Weighted average, ' +
      'reciprocal rank, ensemble, and score-aware strategies. Cross-encoder reranking ' +
      'for precision.',
  },
  {
    epic: 'EPIC 5',
    badgeVariant: 'warning',
    title: 'Agent-Based RAG',
    metrics: [
      'ReAct reasoning',
      '3 specialized tools',
      'Working memory',
    ],
    description:
      'LangChain-based agent with document search, calculator, and retrieval tools. ' +
      'Step-by-step reasoning traces with observable thought process.',
  },
];

function buildCapabilityGrid() {
  const grid = document.createElement('div');
  grid.className = 'grid';

  for (const cap of CAPABILITIES) {
    const card = document.createElement('div');
    card.className = 'card col-4 capability-card';

    const header = document.createElement('div');
    header.className = 'capability-card__header';
    header.appendChild(renderBadge(cap.epic, cap.badgeVariant));

    const title = document.createElement('span');
    title.className = 'capability-card__title';
    title.textContent = cap.title;
    header.appendChild(title);

    const ul = document.createElement('ul');
    ul.className = 'capability-card__metrics';
    for (const m of cap.metrics) {
      const li = document.createElement('li');
      li.textContent = m;
      ul.appendChild(li);
    }

    const desc = document.createElement('p');
    desc.className = 'capability-card__desc';
    desc.textContent = cap.description;

    card.appendChild(header);
    card.appendChild(ul);
    card.appendChild(desc);
    grid.appendChild(card);
  }

  return grid;
}

// -- Stats Bar --------------------------------------------------------------

function buildStatsBar() {
  const stats = MOCK_DATA.systemStats;

  const STAT_ITEMS = [
    { value: stats.documents, label: 'Documents' },
    { value: stats.trainingQueries.toLocaleString(), label: 'Training Queries' },
    { value: stats.configurations, label: 'Configurations' },
    { value: '30+', label: 'Components' },
    { value: stats.tests.toLocaleString(), label: 'Tests' },
  ];

  const bar = document.createElement('div');
  bar.className = 'stats-bar';

  for (const item of STAT_ITEMS) {
    const el = document.createElement('div');
    el.className = 'stat-item';

    const valueEl = document.createElement('span');
    valueEl.className = 'stat-item__value';
    valueEl.textContent = String(item.value);

    const labelEl = document.createElement('span');
    labelEl.className = 'stat-item__label';
    labelEl.textContent = item.label;

    el.appendChild(valueEl);
    el.appendChild(labelEl);
    bar.appendChild(el);
  }

  return bar;
}

// -- Tech Stack -------------------------------------------------------------

const TECH_STACK = [
  'Python', 'FastAPI', 'PyTorch', 'FAISS', 'sentence-transformers',
  'Pydantic', 'Chart.js', 'LangChain', 'MLflow', 'Weaviate',
];

function buildTechStack() {
  const section = document.createElement('div');
  section.className = 'tech-stack';

  const title = document.createElement('h3');
  title.textContent = 'Built With';
  section.appendChild(title);

  const row = document.createElement('div');
  row.className = 'tech-stack__badges';

  for (const tech of TECH_STACK) {
    row.appendChild(renderBadge(tech, 'muted'));
  }

  section.appendChild(row);
  return section;
}

// -- CTA --------------------------------------------------------------------

function buildCTA() {
  const wrapper = document.createElement('div');
  wrapper.className = 'cta-wrapper';

  const btn = document.createElement('button');
  btn.className = 'btn btn--accent';
  btn.textContent = 'Try a Query \u2192';
  btn.addEventListener('click', () => navigateTo('query'));

  wrapper.appendChild(btn);
  return wrapper;
}


// ===========================================================================
// QUERY PAGE
// ===========================================================================

const COMPLEXITY_VARIANT = {
  simple: 'accent',
  medium: 'warning',
  complex: 'error',
  agent: 'error',
};

export function renderQueryPage() {
  const container = document.getElementById('query-content');
  if (!container) return;
  container.innerHTML = '';

  const grid = document.createElement('div');
  grid.className = 'grid';

  const leftPanel = document.createElement('div');
  leftPanel.className = 'col-4';

  const rightPanel = document.createElement('div');
  rightPanel.className = 'col-8';

  grid.appendChild(leftPanel);
  grid.appendChild(rightPanel);
  container.appendChild(grid);

  // Left panel
  buildQueryInput(leftPanel);
  buildExampleQueries(leftPanel);
  buildModeIndicator(leftPanel);

  // Right panel (empty state)
  showEmptyState(rightPanel);

  // Reactive subscriptions
  AppState.on('queryResult', (result) => {
    if (!result) return;
    renderResults(rightPanel, result);
  });

  AppState.on('isLoading', (loading) => {
    const btn = leftPanel.querySelector('.query-submit-btn');
    if (btn) {
      btn.disabled = loading;
      btn.textContent = loading ? 'Processing...' : 'Submit Query';
    }
  });
}

function buildQueryInput(panel) {
  const textarea = document.createElement('textarea');
  textarea.className = 'query-input';
  textarea.rows = 4;
  textarea.placeholder = 'Ask a question about RISC-V architecture...';

  const selector = document.createElement('div');
  selector.className = 'strategy-selector';

  const strategies = [
    { value: 'cost_optimized', label: 'Cost Optimized' },
    { value: 'balanced', label: 'Balanced' },
    { value: 'quality_first', label: 'Quality First' },
  ];

  for (const strat of strategies) {
    const option = document.createElement('div');
    option.className = 'strategy-option';

    const input = document.createElement('input');
    input.type = 'radio';
    input.name = 'strategy';
    input.id = 'strategy-' + strat.value;
    input.value = strat.value;
    if (strat.value === 'balanced') input.checked = true;

    const label = document.createElement('label');
    label.htmlFor = 'strategy-' + strat.value;
    label.textContent = strat.label;

    option.appendChild(input);
    option.appendChild(label);
    selector.appendChild(option);
  }

  const submitBtn = document.createElement('button');
  submitBtn.className = 'btn btn--accent btn--full query-submit-btn';
  submitBtn.textContent = 'Submit Query';

  submitBtn.addEventListener('click', () => {
    const text = textarea.value.trim();
    if (!text) return;
    const selected = panel.querySelector('input[name="strategy"]:checked');
    const strategy = selected ? selected.value : 'balanced';
    submitQuery(text, strategy);
  });

  panel.appendChild(textarea);
  panel.appendChild(selector);
  panel.appendChild(submitBtn);
}

function buildExampleQueries(panel) {
  const section = document.createElement('div');
  section.className = 'example-queries';

  const title = document.createElement('h3');
  title.className = 'result-section__title';
  title.textContent = 'Example Queries';
  section.appendChild(title);

  for (const eq of MOCK_DATA.exampleQueries) {
    const row = document.createElement('div');
    row.className = 'example-query';

    const label = document.createElement('span');
    label.className = 'example-query__label';
    label.textContent = eq.label;

    const badge = renderBadge(eq.type, COMPLEXITY_VARIANT[eq.type] || 'muted');

    row.appendChild(label);
    row.appendChild(badge);

    row.addEventListener('click', () => {
      const textarea = panel.querySelector('.query-input');
      if (textarea) textarea.value = eq.query;
      const selected = panel.querySelector('input[name="strategy"]:checked');
      const strategy = selected ? selected.value : 'balanced';
      submitQuery(eq.query, strategy);
    });

    section.appendChild(row);
  }

  panel.appendChild(section);
}

function buildModeIndicator(panel) {
  const indicator = document.createElement('div');
  indicator.className = 'mode-indicator';
  indicator.textContent = AppState.get('mode') === 'demo' ? 'DEMO MODE' : 'LIVE MODE';

  AppState.on('mode', (mode) => {
    indicator.textContent = mode === 'demo' ? 'DEMO MODE' : 'LIVE MODE';
  });

  panel.appendChild(indicator);
}

function showEmptyState(panel) {
  panel.innerHTML = '';
  const empty = document.createElement('div');
  empty.className = 'results-empty';
  empty.textContent = 'Submit a query to see results';
  panel.appendChild(empty);
}

function renderResults(panel, result) {
  panel.innerHTML = '';

  // 1. Pipeline Timing
  const timingSection = createResultSection('');
  renderPipelineTiming(timingSection, result.processingTime);
  panel.appendChild(timingSection);

  // 2. Answer Card
  const answerCard = document.createElement('div');
  answerCard.className = 'card';

  const answerText = document.createElement('div');
  answerText.className = 'answer-text';
  answerText.textContent = result.answer;
  answerCard.appendChild(answerText);

  renderConfidenceGauge(answerCard, result.confidence);
  panel.appendChild(answerCard);

  // 3. Complexity Radar
  const complexitySection = createResultSection('Query Complexity Analysis');
  const complexityHeader = complexitySection.querySelector('.result-section__title');
  if (complexityHeader) {
    complexityHeader.appendChild(
      renderBadge(result.complexity.label, COMPLEXITY_VARIANT[result.complexity.label] || 'muted')
    );
  }

  const scoreText = document.createElement('div');
  scoreText.style.cssText = 'margin-bottom: var(--sp-4); font-family: var(--font-mono); color: var(--text-secondary);';
  scoreText.textContent = 'Overall: ' + (result.complexity.overall * 100).toFixed(0) + '%';
  complexitySection.appendChild(scoreText);

  const chartContainer = document.createElement('div');
  chartContainer.className = 'chart-container chart-container--half';
  chartContainer.id = 'complexity-radar';
  complexitySection.appendChild(chartContainer);

  panel.appendChild(complexitySection);

  requestAnimationFrame(() => {
    const scores = result.complexity.scores;
    createRadarChart(
      'complexity-radar',
      ['Technical', 'Linguistic', 'Semantic', 'Computational', 'Task'],
      [{
        label: 'Query Profile',
        data: [scores.technical, scores.linguistic, scores.semantic, scores.computational, scores.task],
      }]
    );
  });

  // 4. Retrieved Sources
  const sourcesSection = createResultSection('Retrieved Sources');
  const sourcesHeader = sourcesSection.querySelector('.result-section__title');
  if (sourcesHeader) {
    sourcesHeader.appendChild(renderBadge(String(result.sources.length), 'muted'));
  }

  const sourcesContainer = document.createElement('div');
  result.sources.forEach((source, index) => {
    renderSourceCard(sourcesContainer, source, index + 1);
  });
  sourcesSection.appendChild(sourcesContainer);
  panel.appendChild(sourcesSection);

  // 5. Cost Breakdown
  const costSection = createResultSection('Cost Analysis');
  const costHeader = costSection.querySelector('.result-section__title');
  if (costHeader) {
    costHeader.appendChild(renderBadge(result.strategy, 'accent'));
    costHeader.appendChild(renderBadge(result.model, 'muted'));
  }

  const costContainer = document.createElement('div');
  renderCostBreakdown(costContainer, result.cost);
  costSection.appendChild(costContainer);
  panel.appendChild(costSection);

  // 6. Reasoning Trace (agent queries only)
  if (result.reasoningSteps && result.reasoningSteps.length > 0) {
    const reasoningSection = createResultSection('Agent Reasoning Trace');
    const reasoningHeader = reasoningSection.querySelector('.result-section__title');
    if (reasoningHeader) {
      reasoningHeader.appendChild(renderBadge(String(result.reasoningSteps.length) + ' steps', 'warning'));
    }

    const timelineContainer = document.createElement('div');
    timelineContainer.className = 'timeline';

    for (const step of result.reasoningSteps) {
      renderReasoningStep(timelineContainer, step);
    }

    reasoningSection.appendChild(timelineContainer);
    panel.appendChild(reasoningSection);
  }
}

function createResultSection(titleText) {
  const section = document.createElement('div');
  section.className = 'result-section';

  if (titleText) {
    const title = document.createElement('div');
    title.className = 'result-section__title';
    title.textContent = titleText;
    section.appendChild(title);
  }

  return section;
}


// ===========================================================================
// CORPUS PAGE
// ===========================================================================

const CATEGORY_COLORS = ['#00d46a', '#60a5fa', '#f59e0b'];

export function renderCorpusPage() {
  const container = document.getElementById('corpus-content');
  if (!container) return;
  container.innerHTML = '';

  container.appendChild(buildCorpusHeader());
  container.appendChild(buildCorpusChartsRow());
  container.appendChild(buildDocumentTree());
  container.appendChild(buildMetadataPanel());
}

function buildCorpusHeader() {
  const header = document.createElement('div');
  header.className = 'section';

  const title = document.createElement('h1');
  title.className = 'page-title';
  title.textContent = 'Corpus Explorer';

  const subtitle = document.createElement('p');
  subtitle.className = 'page-subtitle';
  subtitle.textContent =
    MOCK_DATA.corpus.totalDocuments +
    ' RISC-V technical documents across ' +
    MOCK_DATA.corpus.categories.length +
    ' categories';

  header.appendChild(title);
  header.appendChild(subtitle);
  return header;
}

function buildCorpusChartsRow() {
  const row = document.createElement('div');
  row.className = 'grid corpus-charts';

  // Left: doughnut
  const leftCol = document.createElement('div');
  leftCol.className = 'col-6';

  const doughnutTitle = document.createElement('h3');
  doughnutTitle.className = 'section-title';
  doughnutTitle.textContent = 'Category Distribution';
  leftCol.appendChild(doughnutTitle);

  const doughnutContainer = document.createElement('div');
  doughnutContainer.id = 'corpus-doughnut';
  doughnutContainer.className = 'chart-container chart-container--half';
  leftCol.appendChild(doughnutContainer);

  const categories = MOCK_DATA.corpus.categories;
  const labels = categories.map((c) => c.name);
  const data = categories.map((c) => c.count);

  requestAnimationFrame(() => {
    createDoughnutChart('corpus-doughnut', labels, data, CATEGORY_COLORS);
  });

  // Legend
  const legend = document.createElement('div');
  legend.className = 'legend-items';

  const total = MOCK_DATA.corpus.totalDocuments;
  categories.forEach((cat, i) => {
    const item = document.createElement('div');
    item.className = 'legend-item';

    const dot = document.createElement('span');
    dot.className = 'legend-item__dot';
    dot.style.backgroundColor = CATEGORY_COLORS[i % CATEGORY_COLORS.length];

    const text = document.createElement('span');
    const pct = ((cat.count / total) * 100).toFixed(0);
    text.textContent = cat.name + ' ' + cat.count + ' (' + pct + '%)';

    item.appendChild(dot);
    item.appendChild(text);
    legend.appendChild(item);
  });

  leftCol.appendChild(legend);
  row.appendChild(leftCol);

  // Right: subcategory bar chart
  const rightCol = document.createElement('div');
  rightCol.className = 'col-6';

  const barTitle = document.createElement('h3');
  barTitle.className = 'section-title';
  barTitle.textContent = 'Subcategory Breakdown';
  rightCol.appendChild(barTitle);

  const barContainer = document.createElement('div');
  barContainer.id = 'corpus-subcategories';
  barContainer.className = 'chart-container';
  rightCol.appendChild(barContainer);

  const subcats = [];
  for (const cat of MOCK_DATA.corpus.categories) {
    for (const sub of cat.subcategories) {
      subcats.push({ name: sub.name + ' (' + cat.name + ')', count: sub.documents.length });
    }
  }
  subcats.sort((a, b) => b.count - a.count);

  requestAnimationFrame(() => {
    createHorizontalBarChart('corpus-subcategories', subcats.map((s) => s.name), subcats.map((s) => s.count));
  });

  row.appendChild(rightCol);
  return row;
}

function buildDocumentTree() {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h3');
  title.className = 'section-title';
  title.textContent = 'Document Browser';
  section.appendChild(title);

  const treeContainer = document.createElement('div');
  treeContainer.className = 'doc-tree';
  treeContainer.id = 'doc-tree';

  for (const cat of MOCK_DATA.corpus.categories) {
    const catNode = buildCategoryNode(cat);
    renderTreeNode(treeContainer, catNode, 0);
  }

  section.appendChild(treeContainer);
  return section;
}

function buildCategoryNode(category) {
  const children = category.subcategories.map((sub) => {
    const docChildren = sub.documents.map((doc) => ({
      name: doc.file,
      children: null,
      metadata: {
        title: doc.title,
        size: doc.size_mb.toFixed(2) + ' MB',
      },
    }));

    return {
      name: sub.name + ' (' + docChildren.length + ')',
      children: docChildren,
    };
  });

  return {
    name: category.name + ' (' + category.count + ')',
    children,
  };
}

function buildMetadataPanel() {
  const panel = document.createElement('div');
  panel.className = 'doc-metadata';
  panel.id = 'doc-metadata';

  const emptyMsg = document.createElement('div');
  emptyMsg.className = 'doc-metadata__empty';
  emptyMsg.textContent = 'Select a document to view details';
  panel.appendChild(emptyMsg);

  requestAnimationFrame(() => {
    const tree = document.getElementById('doc-tree');
    if (!tree) return;

    tree.addEventListener('click', (e) => {
      const row = e.target.closest('.tree-node__row');
      if (!row) return;

      const bullet = row.querySelector('.tree-node__bullet');
      if (!bullet) return;

      const nameSpan = row.querySelector('.tree-node__name');
      if (!nameSpan) return;

      const fileName = nameSpan.textContent;
      const docData = findDocumentByFile(fileName);
      if (docData) {
        showDocumentMetadata(docData);
      }
    });
  });

  return panel;
}

function findDocumentByFile(fileName) {
  for (const cat of MOCK_DATA.corpus.categories) {
    for (const sub of cat.subcategories) {
      for (const doc of sub.documents) {
        if (doc.file === fileName) {
          return {
            title: doc.title,
            file: doc.file,
            size: doc.size_mb.toFixed(2) + ' MB',
            path: sub.path,
            category: cat.name,
          };
        }
      }
    }
  }
  return null;
}

function showDocumentMetadata(doc) {
  const panel = document.getElementById('doc-metadata');
  if (!panel) return;
  panel.innerHTML = '';

  const fields = [
    { label: 'Title', value: doc.title },
    { label: 'File', value: doc.file },
    { label: 'Category', value: doc.category },
    { label: 'Path', value: doc.path },
    { label: 'Size', value: doc.size },
  ];

  for (const field of fields) {
    const row = document.createElement('div');
    row.className = 'doc-metadata__row';

    const label = document.createElement('span');
    label.className = 'doc-metadata__label';
    label.textContent = field.label;

    const value = document.createElement('span');
    value.className = 'doc-metadata__value';
    value.textContent = field.value;

    row.appendChild(label);
    row.appendChild(value);
    panel.appendChild(row);
  }
}
