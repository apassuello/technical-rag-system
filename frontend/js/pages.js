// ---------------------------------------------------------------------------
// pages.js -- Page-level composition (wires components + charts + data)
// ---------------------------------------------------------------------------

import { AppState, navigateTo } from './state.js';
import { MOCK_DATA } from './data.js';
import { submitQuery, compareConfigs, fetchStats, fetchServices, fetchComponents, fetchTrainingMetrics, fetchWithFallback, startService, uploadDocument, indexCorpus } from './api.js';
import {
  renderConfidenceGauge,
  renderBadge,
  renderMetricCard,
  renderDataTable,
  renderSourceCard,
  renderReasoningStep,
  renderTreeNode,
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

// Unsubscribe functions for reactive listeners (prevents leak on re-render)
let _queryCleanups = [];
let _perfCleanups = [];

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

  // Async: replace mock stats with real API data
  fetchStats().then(stats => {
    if (!stats) return;
    const bar = container.querySelector('.stats-bar');
    if (!bar) return;
    const items = bar.querySelectorAll('.stat-item__value');
    const values = [stats.documents, stats.chunks || stats.trainingQueries, stats.configurations, stats.components, stats.tests];
    items.forEach((el, i) => { if (values[i] != null) el.textContent = String(values[i]); });
  });
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
  // Clean up previous listeners before re-render
  _queryCleanups.forEach(fn => fn());
  _queryCleanups = [];

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

  // Reactive subscriptions (store unsubscribe fns to prevent leak)
  _queryCleanups.push(AppState.on('queryResult', (result) => {
    if (!result) return;
    renderResults(rightPanel, result);
  }));

  _queryCleanups.push(AppState.on('isLoading', (loading) => {
    const btn = leftPanel.querySelector('.query-submit-btn');
    if (btn) {
      btn.disabled = loading;
      btn.textContent = loading ? 'Processing...' : 'Submit Query';
    }
  }));
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
    AppState.set('currentQuery', text);
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

  _queryCleanups.push(AppState.on('mode', (mode) => {
    indicator.textContent = mode === 'demo' ? 'DEMO MODE' : 'LIVE MODE';
  }));

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
  scoreText.className = 'complexity-score';
  scoreText.textContent = 'Overall: ' + (result.complexity.overall * 100).toFixed(0) + '%';
  complexitySection.appendChild(scoreText);

  const chartContainer = document.createElement('div');
  chartContainer.className = 'chart-container chart-container--half';
  chartContainer.id = 'complexity-radar';
  complexitySection.appendChild(chartContainer);

  panel.appendChild(complexitySection);

  requestAnimationFrame(() => {
    if (!document.getElementById('complexity-radar')) return;
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

export async function renderCorpusPage() {
  const container = document.getElementById('corpus-content');
  if (!container) return;
  container.innerHTML = '<div class="loading">Loading corpus data...</div>';

  const data = await fetchWithFallback('corpus', null);
  const corpus = data ?? MOCK_DATA.corpus;

  container.innerHTML = '';
  container.appendChild(buildCorpusHeader(corpus));
  container.appendChild(buildCorpusChartsRow(corpus));
  container.appendChild(buildDocumentTree(corpus));
  container.appendChild(buildMetadataPanel(corpus));
}

function buildCorpusHeader(corpus) {
  const header = document.createElement('div');
  header.className = 'section';

  const title = document.createElement('h1');
  title.className = 'page-title';
  title.textContent = 'Corpus Explorer';

  const totalDocs = corpus.totalDocuments ?? corpus.totalDocuments;
  const catCount = (corpus.categories || []).length;

  const subtitle = document.createElement('p');
  subtitle.className = 'page-subtitle';
  subtitle.textContent = totalDocs + ' RISC-V technical documents across ' + catCount + ' categories';

  header.appendChild(title);
  header.appendChild(subtitle);
  return header;
}

function buildCorpusChartsRow(corpus) {
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

  const categories = corpus.categories || [];
  const labels = categories.map((c) => c.name);
  const data = categories.map((c) => c.count);

  requestAnimationFrame(() => {
    if (!document.getElementById('corpus-doughnut')) return;
    createDoughnutChart('corpus-doughnut', labels, data, CATEGORY_COLORS);
  });

  // Legend
  const legend = document.createElement('div');
  legend.className = 'legend-items';

  const total = corpus.totalDocuments || 1;
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
  for (const cat of (corpus.categories || [])) {
    for (const sub of cat.subcategories) {
      subcats.push({ name: sub.name + ' (' + cat.name + ')', count: sub.documents.length });
    }
  }
  subcats.sort((a, b) => b.count - a.count);

  requestAnimationFrame(() => {
    if (!document.getElementById('corpus-subcategories')) return;
    createHorizontalBarChart('corpus-subcategories', subcats.map((s) => s.name), subcats.map((s) => s.count));
  });

  row.appendChild(rightCol);
  return row;
}

function buildDocumentTree(corpus) {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h3');
  title.className = 'section-title';
  title.textContent = 'Document Browser';
  section.appendChild(title);

  const treeContainer = document.createElement('div');
  treeContainer.className = 'doc-tree';
  treeContainer.id = 'doc-tree';

  for (const cat of (corpus.categories || [])) {
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

function buildMetadataPanel(corpus) {
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
      const docData = findDocumentByFile(fileName, corpus);
      if (docData) {
        showDocumentMetadata(docData);
      }
    });
  });

  return panel;
}

function findDocumentByFile(fileName, corpus) {
  for (const cat of (corpus.categories || [])) {
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


// ===========================================================================
// ARCHITECTURE PAGE
// ===========================================================================

const PIPELINE_STAGES = [
  // Document processing pipeline
  { id: 'pdf', label: 'PDF Corpus', desc: 'Source documents (RISC-V specs, manuals)', type: 'data' },
  { id: 'processor', label: 'Document Processor', desc: 'PDF extraction and chunking', type: 'component', slot: 'processor' },
  { id: 'embedder', label: 'Embedder', desc: 'Text to vector encoding (sentence-transformers)', type: 'component', slot: 'embedder' },
  { id: 'index', label: 'Vector Index', desc: 'FAISS similarity search + BM25 sparse retrieval', type: 'storage' },

  // Query pipeline
  { id: 'query_input', label: 'Query', desc: 'User question input', type: 'data' },
  { id: 'query_processor', label: 'Query Processor', desc: 'ML-based complexity analysis, 5-view scoring', type: 'component', slot: 'query_processor' },
  { id: 'retriever', label: 'Retriever', desc: 'Hybrid search: dense + sparse with fusion and reranking', type: 'component', slot: 'retriever' },
  { id: 'generator', label: 'Generator', desc: 'LLM-powered answer generation with source attribution', type: 'component', slot: 'answer_generator' },
  { id: 'answer', label: 'Answer', desc: 'Generated response with sources and confidence', type: 'data' },
];

const PIPELINE_ROWS = [
  { label: 'Document Pipeline', stages: ['pdf', 'processor', 'embedder', 'index'], flow: 'right' },
  { label: 'Query Pipeline', stages: ['query_input', 'query_processor', 'retriever', 'generator', 'answer'], flow: 'right' },
];

// Cross-pipeline connections (the indexed data feeds retrieval)
const PIPELINE_LINKS = [
  { from: 'index', to: 'retriever' },
];

function findStage(id) {
  return PIPELINE_STAGES.find(s => s.id === id) || null;
}

export async function renderArchitecturePage() {
  const container = document.getElementById('architecture-content');
  if (!container) return;
  container.innerHTML = '<div class="loading">Loading architecture data...</div>';

  const componentsData = await fetchWithFallback('components', null);

  container.innerHTML = '';
  container.appendChild(buildPipelineDiagramSection(componentsData));
  container.appendChild(buildRegistrySection(componentsData));
}

// -- Pipeline Diagram -------------------------------------------------------

function buildPipelineDiagramSection(componentsData) {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h1');
  title.className = 'page-title';
  title.textContent = 'System Architecture';

  const subtitle = document.createElement('p');
  subtitle.className = 'page-subtitle';
  subtitle.textContent = 'Component pipeline architecture';

  const orchestratorNote = document.createElement('p');
  orchestratorNote.className = 'arch-orchestrator-note';
  orchestratorNote.textContent = 'All components run inside PlatformOrchestrator — no separate microservices.';

  section.appendChild(title);
  section.appendChild(subtitle);
  section.appendChild(orchestratorNote);

  const diagram = document.createElement('div');
  diagram.className = 'arch-diagram arch-diagram--pipeline';

  const detail = document.createElement('div');
  detail.className = 'arch-detail';
  detail.style.display = 'none';
  detail.id = 'arch-detail';

  let activeBox = null;

  // Build health lookup from live component data
  const healthMap = {};
  if (componentsData && componentsData.active) {
    for (const [slot, info] of Object.entries(componentsData.active)) {
      healthMap[slot] = info.healthy;
    }
  }

  for (let rowIdx = 0; rowIdx < PIPELINE_ROWS.length; rowIdx++) {
    const rowDef = PIPELINE_ROWS[rowIdx];

    const pipelineRow = document.createElement('div');
    pipelineRow.className = 'pipeline-row';

    const rowLabel = document.createElement('div');
    rowLabel.className = 'pipeline-label';
    rowLabel.textContent = rowDef.label;
    pipelineRow.appendChild(rowLabel);

    const stagesContainer = document.createElement('div');
    stagesContainer.className = 'pipeline-stages';

    for (let i = 0; i < rowDef.stages.length; i++) {
      const stageId = rowDef.stages[i];
      const stage = findStage(stageId);
      if (!stage) continue;

      // Arrow before each stage (except the first)
      if (i > 0) {
        const arrow = document.createElement('div');
        arrow.className = 'pipeline-arrow';
        arrow.innerHTML = '<svg width="24" height="16" viewBox="0 0 24 16"><path d="M0 8h20M16 2l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';
        stagesContainer.appendChild(arrow);
      }

      const box = document.createElement('div');
      box.className = 'arch-box arch-box--' + stage.type;
      box.dataset.stageId = stage.id;

      const label = document.createElement('span');
      label.className = 'arch-box__label';
      label.textContent = stage.label;
      box.appendChild(label);

      const typeTag = document.createElement('span');
      typeTag.className = 'arch-box__type-tag';
      typeTag.textContent = stage.type;
      box.appendChild(typeTag);

      // Health dot overlay for component stages
      if (stage.slot && stage.slot in healthMap) {
        const dot = document.createElement('span');
        dot.className = 'arch-health-dot arch-health-dot--' + (healthMap[stage.slot] ? 'ok' : 'err');
        box.appendChild(dot);
      }

      box.addEventListener('click', () => {
        if (activeBox) activeBox.classList.remove('active');
        if (activeBox === box) {
          activeBox = null;
          detail.style.display = 'none';
          return;
        }
        box.classList.add('active');
        activeBox = box;
        showStageDetail(detail, stage, healthMap);
      });

      stagesContainer.appendChild(box);
    }

    pipelineRow.appendChild(stagesContainer);
    diagram.appendChild(pipelineRow);

    // Cross-pipeline link indicator between rows
    if (rowIdx < PIPELINE_ROWS.length - 1) {
      const linkRow = document.createElement('div');
      linkRow.className = 'pipeline-cross-link';

      // Find links between this row and the next
      const currentStageIds = new Set(rowDef.stages);
      const nextStageIds = new Set(PIPELINE_ROWS[rowIdx + 1].stages);
      const relevantLinks = PIPELINE_LINKS.filter(
        link => currentStageIds.has(link.from) && nextStageIds.has(link.to)
      );

      if (relevantLinks.length > 0) {
        const linkLabel = document.createElement('span');
        linkLabel.className = 'pipeline-cross-link__label';
        linkLabel.textContent = relevantLinks.map(l => {
          const fromStage = findStage(l.from);
          const toStage = findStage(l.to);
          return (fromStage ? fromStage.label : l.from) + ' \u2192 ' + (toStage ? toStage.label : l.to);
        }).join(', ');

        const linkArrow = document.createElement('div');
        linkArrow.className = 'pipeline-cross-link__arrow';
        linkArrow.innerHTML = '<svg width="16" height="24" viewBox="0 0 16 24"><path d="M8 0v20M2 16l6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';

        linkRow.appendChild(linkArrow);
        linkRow.appendChild(linkLabel);
      }

      diagram.appendChild(linkRow);
    }
  }

  section.appendChild(diagram);
  section.appendChild(detail);
  return section;
}

function showStageDetail(panel, stage, healthMap) {
  panel.innerHTML = '';
  panel.style.display = 'block';

  const titleRow = document.createElement('div');
  titleRow.className = 'arch-detail__title';
  titleRow.textContent = stage.label;

  if (stage.slot) {
    titleRow.appendChild(document.createTextNode(' '));
    titleRow.appendChild(renderBadge('slot: ' + stage.slot, 'muted'));
  }

  const desc = document.createElement('div');
  desc.className = 'arch-detail__desc';
  desc.textContent = stage.desc;

  const metaRow = document.createElement('div');
  metaRow.className = 'arch-detail__components';
  metaRow.appendChild(renderBadge(stage.type, stage.type === 'component' ? 'accent' : stage.type === 'storage' ? 'info' : 'muted'));

  if (stage.slot && stage.slot in healthMap) {
    metaRow.appendChild(renderBadge(healthMap[stage.slot] ? 'healthy' : 'unhealthy', healthMap[stage.slot] ? 'accent' : 'error'));
  }

  panel.appendChild(titleRow);
  panel.appendChild(desc);
  panel.appendChild(metaRow);
}

// -- Component Registry -----------------------------------------------------

function buildRegistrySection(componentsData) {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h3');
  title.className = 'section-title';
  title.textContent = 'Component Registry';
  section.appendChild(title);

  const registry = document.createElement('div');
  registry.className = 'component-registry';

  // Use live factory data if available, fall back to mock
  if (componentsData && componentsData.available) {
    const available = componentsData.available;
    for (const [category, types] of Object.entries(available)) {
      if (!Array.isArray(types)) continue;
      const items = types.map(t => ({
        type: typeof t === 'string' ? t : (t.type || String(t)),
        children: null,
        metadata: {},
      }));
      renderTreeNode(registry, {
        name: category + ' (' + items.length + ')',
        children: items,
      }, 0);
    }
    section.appendChild(registry);
    return section;
  }

  const reg = MOCK_DATA.componentRegistry;

  const topCategories = [
    { name: 'Processors', items: reg.processors },
    { name: 'Embedders', items: reg.embedders },
    { name: 'Retrievers', items: reg.retrievers },
    { name: 'Generators', items: reg.generators },
    { name: 'Query Processors', items: reg.queryProcessors },
  ];

  for (const cat of topCategories) {
    const node = buildRegistryTreeNode(cat.name, cat.items);
    renderTreeNode(registry, node, 0);
  }

  const subComponentCategories = [
    { name: 'Query Analyzers', items: reg.subComponents.queryAnalyzers },
    { name: 'LLM Adapters', items: reg.subComponents.llmAdapters },
    { name: 'Fusion Strategies', items: reg.subComponents.fusionStrategies },
    { name: 'Rerankers', items: reg.subComponents.rerankers },
    { name: 'Tools', items: reg.subComponents.tools },
    { name: 'Memory', items: reg.subComponents.memory },
  ];

  const subChildren = subComponentCategories.map(cat => buildRegistryTreeNode(cat.name, cat.items));
  const totalSubCount = subComponentCategories.reduce((sum, cat) => sum + cat.items.length, 0);

  renderTreeNode(registry, {
    name: 'Sub-Components (' + totalSubCount + ')',
    children: subChildren,
  }, 0);

  section.appendChild(registry);
  return section;
}

function buildRegistryTreeNode(categoryName, items) {
  const children = items.map(item => ({
    name: item.type,
    children: null,
    metadata: Object.assign(
      {},
      item.class ? { class: item.class } : {},
      item.description ? { info: item.description } : {}
    ),
  }));

  return {
    name: categoryName + ' (' + items.length + ')',
    children,
  };
}



// ===========================================================================
// PERFORMANCE PAGE
// ===========================================================================

export async function renderPerformancePage() {
  _perfCleanups.forEach(fn => fn());
  _perfCleanups = [];

  const container = document.getElementById('performance-content');
  if (!container) return;
  container.innerHTML = '<div class="loading">Loading training metrics...</div>';

  const data = await fetchWithFallback('metrics/training', null);
  const metrics = data?.modelMetrics ?? MOCK_DATA.modelMetrics;
  const queries = data?.trainingQueries ?? MOCK_DATA.trainingQueries;
  const totalQueries = data?.totalTrainingQueries ?? 679;

  container.innerHTML = '';

  // Runtime metrics first — what the user cares about during a session
  container.appendChild(buildRuntimeMetricsSection());
  container.appendChild(buildConfigComparisonTool());

  // Training metrics in a collapsible section
  container.appendChild(buildTrainingSection(metrics, queries, totalQueries));
}

// -- Runtime Metrics --------------------------------------------------------

function buildRuntimeMetricsSection() {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h1');
  title.className = 'page-title';
  title.textContent = 'Performance Dashboard';
  section.appendChild(title);

  const subtitle = document.createElement('p');
  subtitle.className = 'page-subtitle';
  subtitle.textContent = 'Live query and indexing metrics from this session';
  section.appendChild(subtitle);

  const grid = document.createElement('div');
  grid.className = 'grid metrics-grid';

  // Session stats from query history
  const history = _queryHistory;
  const avgTime = history.length > 0
    ? Math.round(history.reduce((s, h) => s + h.total, 0) / history.length)
    : 0;
  const avgRetrieval = history.length > 0
    ? Math.round(history.reduce((s, h) => s + h.retrieval, 0) / history.length)
    : 0;
  const avgGeneration = history.length > 0
    ? Math.round(history.reduce((s, h) => s + h.generation, 0) / history.length)
    : 0;

  const cards = [
    ['Queries This Session', String(history.length), ''],
    ['Avg Response Time', String(avgTime), 'ms'],
    ['Avg Retrieval', String(avgRetrieval), 'ms'],
    ['Avg Generation', String(avgGeneration), 'ms'],
  ];

  for (const [label, value, unit] of cards) {
    const col = document.createElement('div');
    col.className = 'col-4';
    renderMetricCard(col, label, value, unit);
    grid.appendChild(col);
  }

  section.appendChild(grid);

  // Query history table
  if (history.length > 0) {
    const histTitle = document.createElement('h3');
    histTitle.className = 'section-title';
    histTitle.textContent = 'Query History';
    section.appendChild(histTitle);

    const tableContainer = document.createElement('div');
    const headers = ['Query', 'Complexity', 'Retrieval', 'Generation', 'Total'];
    const rows = history.map(h => [
      h.query.length > 50 ? h.query.substring(0, 50) + '...' : h.query,
      renderBadge(h.complexity, { simple: 'accent', medium: 'warning', complex: 'error' }[h.complexity] || 'muted'),
      h.retrieval + 'ms',
      h.generation + 'ms',
      h.total + 'ms',
    ]);
    renderDataTable(tableContainer, headers, rows);
    section.appendChild(tableContainer);
  } else {
    const empty = document.createElement('div');
    empty.className = 'setup-empty';
    empty.textContent = 'No queries yet. Use the Query page to run queries and see performance data here.';
    section.appendChild(empty);
  }

  // Indexing stats
  fetchStats().then(stats => {
    if (!stats) return;
    const indexInfo = document.createElement('div');
    indexInfo.className = 'perf-index-info';
    indexInfo.innerHTML = '<span class="perf-index-info__label">Indexed:</span> '
      + '<strong>' + (stats.chunks || 0) + '</strong> chunks from '
      + '<strong>' + (stats.documents || 0) + '</strong> PDFs';
    section.insertBefore(indexInfo, grid.nextSibling);
  });

  return section;
}

// Global query history tracker
const _queryHistory = [];

// Hook into query results to track history
AppState.on('queryResult', (result) => {
  if (!result) return;
  _queryHistory.push({
    query: AppState.get('currentQuery') || '(unknown)',
    complexity: result.complexity?.label || 'medium',
    retrieval: result.processingTime?.retrieval || 0,
    generation: result.processingTime?.generation || 0,
    total: (result.processingTime?.retrieval || 0) + (result.processingTime?.generation || 0) + (result.processingTime?.analysis || 0),
    timestamp: Date.now(),
  });
});

// -- Training Section (collapsible) -----------------------------------------

function buildTrainingSection(metrics, queries, totalQueries) {
  const wrapper = document.createElement('div');
  wrapper.className = 'section';

  const toggle = document.createElement('button');
  toggle.className = 'training-toggle';
  toggle.innerHTML = '<span class="training-toggle__icon">\u25B6</span> Training Metrics <span class="badge badge--muted">ML Model</span>';

  const content = document.createElement('div');
  content.className = 'training-content';
  content.style.display = 'none';

  toggle.addEventListener('click', () => {
    const visible = content.style.display !== 'none';
    content.style.display = visible ? 'none' : 'block';
    toggle.querySelector('.training-toggle__icon').textContent = visible ? '\u25B6' : '\u25BC';
  });

  content.appendChild(buildModelAccuracyHero(metrics));
  content.appendChild(buildFeatureImportanceSection(metrics));
  content.appendChild(buildFusionComparisonSection(metrics));
  content.appendChild(buildTrainingDatasetExplorer(queries, totalQueries));
  content.appendChild(buildCostStrategySection());

  wrapper.appendChild(toggle);
  wrapper.appendChild(content);
  return wrapper;
}

// -- Model Accuracy Hero ----------------------------------------------------

function buildModelAccuracyHero(metrics) {
  const section = document.createElement('section');
  section.className = 'section';

  const hero = document.createElement('div');
  hero.className = 'perf-hero';

  const heroValue = document.createElement('div');
  heroValue.className = 'perf-hero__value';
  heroValue.textContent = (metrics.val_accuracy * 100).toFixed(2) + '%';

  const heroLabel = document.createElement('div');
  heroLabel.className = 'perf-hero__label';
  heroLabel.textContent = 'Classification Accuracy (Validation)';

  hero.appendChild(heroValue);
  hero.appendChild(heroLabel);
  section.appendChild(hero);

  const grid = document.createElement('div');
  grid.className = 'grid metrics-grid';

  const metricCols = [
    ['Validation MAE', metrics.val_mae.toFixed(3), ''],
    ['Validation R\u00B2', metrics.val_r2.toFixed(3), ''],
    ['Validation Accuracy', (metrics.val_accuracy * 100).toFixed(2), '%'],
    ['Test MAE', metrics.test_mae.toFixed(3), ''],
    ['Test R\u00B2', metrics.test_r2.toFixed(3), ''],
    ['Test Accuracy', (metrics.test_accuracy * 100).toFixed(2), '%'],
  ];

  for (const [label, value, unit] of metricCols) {
    const col = document.createElement('div');
    col.className = 'col-4';
    renderMetricCard(col, label, value, unit);
    grid.appendChild(col);
  }

  section.appendChild(grid);
  return section;
}

// -- Feature Importance -----------------------------------------------------

function buildFeatureImportanceSection(metrics) {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h2');
  title.className = 'section-title';
  title.textContent = 'Feature Importance';
  section.appendChild(title);

  const chartContainer = document.createElement('div');
  chartContainer.id = 'feature-importance';
  chartContainer.className = 'chart-container';
  section.appendChild(chartContainer);

  const importance = metrics.featureImportance || {};
  const sorted = Object.entries(importance).sort((a, b) => b[1] - a[1]);

  const labels = sorted.map(([key]) => key.charAt(0).toUpperCase() + key.slice(1));
  const dataAsPercent = sorted.map(([, val]) => +(val * 100).toFixed(2));

  requestAnimationFrame(() => {
    if (!document.getElementById('feature-importance')) return;
    createHorizontalBarChart('feature-importance', labels, dataAsPercent);
  });

  return section;
}

// -- Fusion Method Comparison -----------------------------------------------

function buildFusionComparisonSection(metrics) {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h2');
  title.className = 'section-title';
  title.textContent = 'Fusion Method Comparison';
  section.appendChild(title);

  const chartContainer = document.createElement('div');
  chartContainer.id = 'fusion-comparison';
  chartContainer.className = 'chart-container';
  section.appendChild(chartContainer);

  const fusion = metrics.fusionComparison || MOCK_DATA.modelMetrics.fusionComparison;
  const wa = fusion.weighted_average;
  const en = fusion.ensemble;

  const chartLabels = [
    'Accuracy (Val)', 'Accuracy (Test)',
    'MAE (Val)', 'MAE (Test)',
    'R\u00B2 (Val)', 'R\u00B2 (Test)',
  ];

  const datasets = [
    { label: 'Weighted Average', data: [wa.val_accuracy, wa.test_accuracy, wa.val_mae, wa.test_mae, wa.val_r2, wa.test_r2] },
    { label: 'Ensemble', data: [en.val_accuracy, en.test_accuracy, en.val_mae, en.test_mae, en.val_r2, en.test_r2] },
  ];

  requestAnimationFrame(() => {
    if (!document.getElementById('fusion-comparison')) return;
    createGroupedBarChart('fusion-comparison', chartLabels, datasets);
  });

  return section;
}

// -- Training Dataset Explorer ----------------------------------------------

function buildTrainingDatasetExplorer(queries, totalQueries) {
  const section = document.createElement('div');
  section.className = 'section';

  const titleRow = document.createElement('div');
  titleRow.className = 'result-section__title';
  titleRow.textContent = 'Training Dataset Explorer';
  titleRow.appendChild(document.createTextNode(' '));
  titleRow.appendChild(renderBadge(queries.length + ' of ' + totalQueries, 'muted'));
  section.appendChild(titleRow);

  const tableContainer = document.createElement('div');
  const headers = ['Query', 'Complexity', 'Confidence', 'Relevance'];

  const rows = queries.map((q) => {
    const truncated = q.query.length > 60 ? q.query.substring(0, 60) + '...' : q.query;
    const variant = { simple: 'accent', medium: 'warning', complex: 'error' }[q.complexity_level] || 'muted';
    return [truncated, renderBadge(q.complexity_level, variant), q.confidence.toFixed(2), q.domain_relevance.toFixed(2)];
  });

  const radarWrapper = document.createElement('div');
  radarWrapper.className = 'training-radar-container hidden';

  const radarQueryLabel = document.createElement('div');
  radarQueryLabel.className = 'training-radar__query';
  radarWrapper.appendChild(radarQueryLabel);

  const radarContainer = document.createElement('div');
  radarContainer.id = 'training-radar';
  radarContainer.className = 'chart-container chart-container--half';
  radarWrapper.appendChild(radarContainer);

  renderDataTable(tableContainer, headers, rows, {
    onRowClick: (_row, index) => {
      const q = queries[index];
      if (!q) return;

      radarQueryLabel.textContent = q.query;
      radarWrapper.classList.remove('hidden');

      createRadarChart('training-radar',
        ['Technical', 'Linguistic', 'Task', 'Semantic', 'Computational'],
        [{ label: 'View Scores', data: [q.view_scores.technical, q.view_scores.linguistic, q.view_scores.task, q.view_scores.semantic, q.view_scores.computational] }]
      );
    },
  });

  section.appendChild(tableContainer);
  section.appendChild(radarWrapper);
  return section;
}

// -- Cost Strategy Comparison -----------------------------------------------

function buildCostStrategySection() {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h2');
  title.className = 'section-title';
  title.textContent = 'Cost Strategy Comparison';
  section.appendChild(title);

  const chartContainer = document.createElement('div');
  chartContainer.id = 'cost-comparison';
  chartContainer.className = 'chart-container';
  section.appendChild(chartContainer);

  requestAnimationFrame(() => {
    if (!document.getElementById('cost-comparison')) return;
    createCostComparisonChart('cost-comparison', ['Cost Optimized', 'Balanced', 'Quality First'], [0.0003, 0.0036, 0.0475]);
  });

  const costNote = document.createElement('div');
  costNote.className = 'cost-note';
  costNote.textContent = '200x cost difference between strategies';
  section.appendChild(costNote);

  return section;
}

// -- Config Comparison Tool -------------------------------------------------

function buildConfigComparisonTool() {
  const section = document.createElement('div');
  section.className = 'section';

  const title = document.createElement('h2');
  title.className = 'section-title';
  title.textContent = 'Configuration Comparison';
  section.appendChild(title);

  const inputRow = document.createElement('div');
  inputRow.className = 'config-compare-input';

  const textarea = document.createElement('textarea');
  textarea.rows = 2;
  textarea.placeholder = 'Enter a query to compare across configurations...';
  textarea.value = 'Explain RISC-V privilege levels';
  inputRow.appendChild(textarea);

  const compareBtn = document.createElement('button');
  compareBtn.className = 'btn btn--accent';
  compareBtn.textContent = 'Compare';
  compareBtn.addEventListener('click', () => {
    const query = textarea.value.trim();
    if (query) compareConfigs(query);
  });
  inputRow.appendChild(compareBtn);

  section.appendChild(inputRow);

  const resultsArea = document.createElement('div');
  resultsArea.id = 'config-compare-results';
  section.appendChild(resultsArea);

  _perfCleanups.push(AppState.on('compareResults', (result) => {
    if (!result || !result.results) return;
    renderConfigCompareResults(resultsArea, result.results);
  }));

  return section;
}

function renderConfigCompareResults(container, results) {
  container.innerHTML = '';

  const grid = document.createElement('div');
  grid.className = 'grid';

  for (const r of results) {
    const col = document.createElement('div');
    col.className = 'col-4';

    const card = document.createElement('div');
    card.className = 'card config-result-card';

    const header = document.createElement('div');
    header.className = 'config-result-card__header';
    header.textContent = r.config;
    card.appendChild(header);

    const modelRow = document.createElement('div');
    modelRow.className = 'config-result-card__model';
    modelRow.appendChild(renderBadge(r.model, 'info'));
    card.appendChild(modelRow);

    card.appendChild(buildCompareRow('Confidence', (r.confidence * 100).toFixed(1) + '%'));

    const gaugeTrack = document.createElement('div');
    gaugeTrack.className = 'gauge__track config-result-card__gauge';
    const gaugeFill = document.createElement('div');
    gaugeFill.className = 'gauge__fill';
    gaugeFill.style.width = (r.confidence * 100) + '%';
    gaugeTrack.appendChild(gaugeFill);
    card.appendChild(gaugeTrack);

    card.appendChild(buildCompareRow('Top Score', r.topScore.toFixed(2)));
    card.appendChild(buildCompareRow('Timing', r.timing + 'ms'));
    card.appendChild(buildCompareRow('Cost', '$' + r.cost.toFixed(4)));

    const preview = document.createElement('div');
    preview.className = 'config-result-card__preview';
    preview.textContent = r.answerPreview.length > 160 ? r.answerPreview.substring(0, 160) + '...' : r.answerPreview;
    card.appendChild(preview);

    const badgesRow = document.createElement('div');
    badgesRow.className = 'config-result-card__badges';
    badgesRow.appendChild(renderBadge(r.fusion, 'accent'));
    badgesRow.appendChild(renderBadge(r.reranker, 'muted'));
    card.appendChild(badgesRow);

    col.appendChild(card);
    grid.appendChild(col);
  }

  container.appendChild(grid);
}

function buildCompareRow(label, value) {
  const row = document.createElement('div');
  row.className = 'config-result-card__row';

  const labelEl = document.createElement('span');
  labelEl.className = 'config-result-card__label';
  labelEl.textContent = label;

  const valueEl = document.createElement('span');
  valueEl.className = 'config-result-card__value';
  valueEl.textContent = value;

  row.appendChild(labelEl);
  row.appendChild(valueEl);
  return row;
}


// ===========================================================================
// SETUP PAGE
// ===========================================================================

export function renderSetupPage() {
  const container = document.getElementById('setup-content');
  if (!container) return;
  container.innerHTML = '';

  const title = document.createElement('h1');
  title.className = 'page-title';
  title.textContent = 'System Setup';
  container.appendChild(title);

  const subtitle = document.createElement('p');
  subtitle.className = 'page-subtitle';
  subtitle.textContent = 'Configure services, LLM provider, and manage documents';
  container.appendChild(subtitle);

  const grid = document.createElement('div');
  grid.className = 'setup-grid';

  grid.appendChild(buildServicesPanel());
  grid.appendChild(buildLLMPanel());
  grid.appendChild(buildVectorStorePanel());
  grid.appendChild(buildDocumentPanel());
  grid.appendChild(buildConfigExportPanel());
  grid.appendChild(buildComponentStatusPanel());

  container.appendChild(grid);
}

// -- Services Panel ---------------------------------------------------------

function buildServicesPanel() {
  const panel = createSetupPanel('Services', 'Local service status');

  const list = document.createElement('div');
  list.className = 'setup-services';
  list.innerHTML = '<div class="loading">Detecting services...</div>';

  fetchServices().then(data => {
    list.innerHTML = '';
    if (!data) {
      list.innerHTML = '<div class="setup-empty">Unable to detect services</div>';
      return;
    }

    const services = [
      { key: 'ollama', label: 'Ollama', running: data.ollama?.running, models: data.ollama?.models },
      { key: 'llama_server', label: 'llama-server', running: data.llama_server?.running },
      { key: 'weaviate', label: 'Weaviate', running: data.weaviate?.running, warning: 'v3\u2192v4 migration pending' },
    ];

    for (const svc of services) {
      const row = document.createElement('div');
      row.className = 'setup-service-row';

      const info = document.createElement('div');
      info.className = 'setup-service-info';

      const name = document.createElement('span');
      name.className = 'setup-service-name';
      name.textContent = svc.label;
      info.appendChild(name);

      const badge = document.createElement('span');
      badge.className = 'badge badge--' + (svc.running ? 'accent' : 'muted');
      badge.textContent = svc.running ? 'Running' : 'Stopped';
      info.appendChild(badge);

      if (svc.warning) {
        const warn = document.createElement('span');
        warn.className = 'setup-warning';
        warn.textContent = svc.warning;
        info.appendChild(warn);
      }

      row.appendChild(info);

      if (svc.models && svc.models.length > 0) {
        const modelList = document.createElement('div');
        modelList.className = 'setup-models';
        modelList.textContent = 'Models: ' + svc.models.join(', ');
        row.appendChild(modelList);
      }

      if (!svc.running && svc.key !== 'llama_server') {
        const btn = document.createElement('button');
        btn.className = 'btn btn--accent setup-btn';
        btn.textContent = 'Start';
        btn.addEventListener('click', async () => {
          btn.disabled = true;
          btn.textContent = 'Starting...';
          const result = await startService(svc.key);
          if (result && result.status === 'started') {
            badge.className = 'badge badge--accent';
            badge.textContent = 'Running';
            btn.textContent = 'Started';
          } else {
            btn.textContent = 'Failed';
            btn.disabled = false;
          }
        });
        row.appendChild(btn);
      }

      list.appendChild(row);
    }
  });

  panel.appendChild(list);
  return panel;
}

// -- LLM Panel --------------------------------------------------------------

function buildLLMPanel() {
  const panel = createSetupPanel('LLM Configuration', 'Select provider, model, and API key');

  const PROVIDERS = [
    { value: 'local', label: 'llama-server' },
    { value: 'ollama', label: 'Ollama' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'mistral', label: 'Mistral' },
    { value: 'huggingface', label: 'HuggingFace' },
    { value: 'mock', label: 'Mock' },
  ];

  const MODEL_DEFAULTS = {
    local: 'qwen2.5-1.5b-instruct',
    ollama: 'mistral:latest',
    openai: 'gpt-4o-mini',
    anthropic: 'claude-3-haiku-20240307',
    mistral: 'mistral-small-latest',
    huggingface: 'mistralai/Mistral-7B-Instruct-v0.2',
    mock: 'mock-model',
  };

  const CLOUD = new Set(['openai', 'anthropic', 'mistral', 'huggingface']);

  const form = document.createElement('div');
  form.className = 'setup-form';

  // Provider
  const providerSelect = document.createElement('select');
  providerSelect.className = 'config-select';
  for (const p of PROVIDERS) {
    const opt = document.createElement('option');
    opt.value = p.value;
    opt.textContent = p.label;
    providerSelect.appendChild(opt);
  }
  form.appendChild(createFormRow('Provider', providerSelect));

  // Model
  const modelInput = document.createElement('input');
  modelInput.type = 'text';
  modelInput.className = 'query-input setup-text-input';
  modelInput.placeholder = 'Model name';
  form.appendChild(createFormRow('Model', modelInput));

  // API Key
  const keyInput = document.createElement('input');
  keyInput.type = 'password';
  keyInput.className = 'query-input setup-text-input';
  keyInput.placeholder = 'API key (cloud providers only)';
  const keyRow = createFormRow('API Key', keyInput);
  keyRow.style.display = 'none';
  form.appendChild(keyRow);

  // Base URL
  const urlInput = document.createElement('input');
  urlInput.type = 'text';
  urlInput.className = 'query-input setup-text-input';
  urlInput.placeholder = 'http://localhost:11434';
  form.appendChild(createFormRow('Base URL', urlInput));

  // Status + Apply
  const actionRow = document.createElement('div');
  actionRow.className = 'setup-action-row';

  const statusEl = document.createElement('span');
  statusEl.className = 'setup-status';

  const applyBtn = document.createElement('button');
  applyBtn.className = 'btn btn--accent';
  applyBtn.textContent = 'Apply';

  actionRow.appendChild(statusEl);
  actionRow.appendChild(applyBtn);
  form.appendChild(actionRow);

  // Sync visibility
  function syncUI() {
    const provider = providerSelect.value;
    modelInput.value = MODEL_DEFAULTS[provider] || '';
    keyRow.style.display = CLOUD.has(provider) ? '' : 'none';
    // Restore saved key
    const saved = localStorage.getItem('llm_key_' + provider);
    if (saved) keyInput.value = saved;
  }
  providerSelect.addEventListener('change', syncUI);

  applyBtn.addEventListener('click', async () => {
    const provider = providerSelect.value;
    const body = { provider, model: modelInput.value };
    if (keyInput.value) {
      body.api_key = keyInput.value;
      localStorage.setItem('llm_key_' + provider, keyInput.value);
    }
    if (urlInput.value) body.base_url = urlInput.value;

    statusEl.textContent = 'Applying...';
    statusEl.className = 'setup-status';

    try {
      const res = await fetch('/api/v1/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        statusEl.textContent = 'Applied';
        statusEl.className = 'setup-status setup-status--ok';
        if (window._refreshLLMHeader) window._refreshLLMHeader();
      } else {
        statusEl.textContent = 'Failed';
        statusEl.className = 'setup-status setup-status--err';
      }
    } catch {
      statusEl.textContent = 'Error';
      statusEl.className = 'setup-status setup-status--err';
    }
  });

  // Initialize from backend
  fetch('/api/v1/status').then(r => r.json()).then(data => {
    if (data.llm) {
      providerSelect.value = data.llm.provider || 'mock';
      modelInput.value = data.llm.model || '';
      keyRow.style.display = CLOUD.has(providerSelect.value) ? '' : 'none';
    }
  }).catch(() => {});

  panel.appendChild(form);
  return panel;
}

// -- Vector Store Panel -----------------------------------------------------

function buildVectorStorePanel() {
  const panel = createSetupPanel('Vector Store', 'Select backend for document storage');

  const saved = localStorage.getItem('vectorStore') || 'faiss';

  const options = document.createElement('div');
  options.className = 'setup-radio-group';

  const faissOpt = createRadioOption('vector-store', 'faiss', 'FAISS (In-Memory)', saved === 'faiss');
  const weavOpt = createRadioOption('vector-store', 'weaviate', 'Weaviate (Docker)', saved === 'weaviate');

  options.appendChild(faissOpt);
  options.appendChild(weavOpt);

  const statusEl = document.createElement('div');
  statusEl.className = 'setup-status';

  // Check Weaviate availability
  const weavNote = document.createElement('div');
  weavNote.className = 'setup-note';
  weavNote.textContent = 'Checking Weaviate status...';

  fetchServices().then(data => {
    const running = data?.weaviate?.running;
    if (running) {
      weavNote.textContent = 'Weaviate is running (Docker container detected)';
      weavNote.className = 'setup-note setup-note--ok';
    } else {
      weavNote.textContent = 'Weaviate not detected. Start the Docker container: docker compose up -d';
      weavNote.className = 'setup-note setup-note--warn';
    }
  });

  // Handle selection change
  options.addEventListener('change', (e) => {
    const value = e.target.value;
    localStorage.setItem('vectorStore', value);
    AppState.set('vectorStore', value);
    statusEl.textContent = 'Selected: ' + (value === 'faiss' ? 'FAISS' : 'Weaviate');
    statusEl.className = 'setup-status setup-status--ok';

    // If weaviate selected, check it's running
    if (value === 'weaviate') {
      fetchServices().then(data => {
        if (!data?.weaviate?.running) {
          statusEl.textContent = 'Weaviate not running — start Docker container first';
          statusEl.className = 'setup-status setup-status--err';
        }
      });
    }
  });

  panel.appendChild(options);
  panel.appendChild(weavNote);
  panel.appendChild(statusEl);
  return panel;
}

// -- Config Export/Import Panel ----------------------------------------------

function buildConfigExportPanel() {
  const panel = createSetupPanel('Configuration', 'Export or import pipeline settings as YAML');

  const btnRow = document.createElement('div');
  btnRow.className = 'setup-form-row';

  // Export button — downloads current settings as YAML
  const exportBtn = document.createElement('button');
  exportBtn.className = 'btn btn--accent';
  exportBtn.textContent = 'Export YAML';
  exportBtn.addEventListener('click', async () => {
    const status = await fetch('/api/v1/status').then(r => r.json()).catch(() => null);
    const vectorStore = localStorage.getItem('vectorStore') || 'faiss';
    const config = {
      answer_generator: {
        type: 'adaptive_modular',
        config: {
          llm_client: {
            type: status?.llm?.provider || 'mock',
            config: { model_name: status?.llm?.model || 'mock-model' },
          },
        },
      },
      retriever: { type: 'modular_unified', config: { backend: vectorStore } },
      query_processor: { type: 'modular' },
    };
    if (status?.llm?.base_url) {
      config.answer_generator.config.llm_client.config.base_url = status.llm.base_url;
    }

    // Simple YAML serialization
    const yaml = configToYaml(config);
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'rag-config.yaml';
    a.click();
    URL.revokeObjectURL(a.href);
  });

  // Import button — loads YAML and applies settings
  const importBtn = document.createElement('button');
  importBtn.className = 'btn';
  importBtn.textContent = 'Import YAML';
  const importInput = document.createElement('input');
  importInput.type = 'file';
  importInput.accept = '.yaml,.yml';
  importInput.style.display = 'none';

  importBtn.addEventListener('click', () => importInput.click());
  importInput.addEventListener('change', async () => {
    const file = importInput.files[0];
    if (!file) return;
    const text = await file.text();
    const result = await fetch('/api/v1/config/import', {
      method: 'POST',
      headers: { 'Content-Type': 'text/yaml' },
      body: text,
    }).then(r => r.json()).catch(() => null);

    const statusEl = panel.querySelector('.setup-status') || document.createElement('div');
    statusEl.className = 'setup-status';
    if (result?.status === 'ok') {
      statusEl.textContent = 'Config imported and applied';
      statusEl.className = 'setup-status setup-status--ok';
      if (window._refreshLLMHeader) window._refreshLLMHeader();
    } else {
      statusEl.textContent = 'Import failed: ' + (result?.detail || 'unknown error');
      statusEl.className = 'setup-status setup-status--err';
    }
    if (!panel.querySelector('.setup-status')) panel.appendChild(statusEl);
  });

  btnRow.appendChild(exportBtn);
  btnRow.appendChild(importBtn);
  btnRow.appendChild(importInput);
  panel.appendChild(btnRow);

  const note = document.createElement('div');
  note.className = 'setup-note';
  note.textContent = 'Export saves current LLM and vector store settings. Import applies a YAML config file.';
  panel.appendChild(note);

  return panel;
}

function configToYaml(obj, indent) {
  indent = indent || 0;
  const pad = '  '.repeat(indent);
  let out = '';
  for (const [k, v] of Object.entries(obj)) {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      out += pad + k + ':\n' + configToYaml(v, indent + 1);
    } else {
      out += pad + k + ': ' + JSON.stringify(v) + '\n';
    }
  }
  return out;
}

// -- Document Management Panel ----------------------------------------------

function buildDocumentPanel() {
  const panel = createSetupPanel('Document Management', 'Upload PDFs or index the full corpus');

  // Index corpus button
  const indexRow = document.createElement('div');
  indexRow.className = 'setup-form-row';

  const indexBtn = document.createElement('button');
  indexBtn.className = 'btn btn--primary';
  indexBtn.textContent = 'Index Corpus';

  const indexStatus = document.createElement('span');
  indexStatus.className = 'setup-index-status';

  // Check current state and show it
  fetchStats().then(stats => {
    if (stats && stats.chunks > 0) {
      indexStatus.textContent = stats.chunks + ' chunks indexed from ' + stats.documents + ' PDFs';
      indexStatus.className = 'setup-index-status setup-index-status--ok';
    } else if (stats) {
      indexStatus.textContent = stats.documents + ' PDFs available, 0 indexed';
    }
  });

  indexBtn.addEventListener('click', async () => {
    indexBtn.disabled = true;
    indexBtn.textContent = 'Indexing...';
    indexStatus.textContent = 'Processing PDFs (this may take a minute)...';
    indexStatus.className = 'setup-index-status';
    const result = await indexCorpus();
    indexBtn.disabled = false;
    indexBtn.textContent = 'Index Corpus';
    if (result && result.status === 'ok') {
      const cached = result.fromCache ? ' (cached)' : '';
      indexStatus.textContent = result.totalChunks + ' chunks from ' + result.totalDocs + ' files' + cached;
      indexStatus.className = 'setup-index-status setup-index-status--ok';
    } else {
      indexStatus.textContent = 'Indexing failed';
      indexStatus.className = 'setup-index-status setup-index-status--err';
    }
  });

  indexRow.appendChild(indexBtn);
  indexRow.appendChild(indexStatus);
  panel.appendChild(indexRow);

  // Separator
  const hr = document.createElement('hr');
  hr.style.cssText = 'border:none;border-top:1px solid var(--border);margin:var(--sp-4) 0';
  panel.appendChild(hr);

  // Upload dropzone
  const dropzone = document.createElement('div');
  dropzone.className = 'setup-dropzone';
  dropzone.textContent = 'Drop PDF here or click to upload';

  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.pdf';
  fileInput.style.display = 'none';

  const resultArea = document.createElement('div');
  resultArea.className = 'setup-upload-result';

  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file, resultArea);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleUpload(fileInput.files[0], resultArea);
  });

  panel.appendChild(dropzone);
  panel.appendChild(fileInput);
  panel.appendChild(resultArea);
  return panel;
}

async function handleUpload(file, resultArea) {
  resultArea.textContent = 'Uploading ' + file.name + '...';
  const result = await uploadDocument(file);
  if (result) {
    resultArea.textContent = file.name + ' \u2014 ' + (result.chunks || 0) + ' chunks indexed';
    resultArea.className = 'setup-upload-result setup-upload-result--ok';
  } else {
    resultArea.textContent = 'Upload failed';
    resultArea.className = 'setup-upload-result setup-upload-result--err';
  }
}

// -- Component Status Panel -------------------------------------------------

function buildComponentStatusPanel() {
  const panel = createSetupPanel('Component Status', 'Live component health');

  const table = document.createElement('div');
  table.className = 'setup-component-table';
  table.innerHTML = '<div class="loading">Loading components...</div>';

  fetchComponents().then(data => {
    table.innerHTML = '';
    if (!data || !data.active) {
      table.innerHTML = '<div class="setup-empty">System not initialized</div>';
      return;
    }

    // Header
    const header = document.createElement('div');
    header.className = 'setup-comp-row setup-comp-header';
    for (const h of ['Slot', 'Type', 'Health']) {
      const cell = document.createElement('span');
      cell.textContent = h;
      header.appendChild(cell);
    }
    table.appendChild(header);

    for (const [slot, info] of Object.entries(data.active)) {
      const row = document.createElement('div');
      row.className = 'setup-comp-row';

      const slotEl = document.createElement('span');
      slotEl.className = 'setup-comp-slot';
      slotEl.textContent = slot;

      const typeEl = document.createElement('span');
      typeEl.className = 'setup-comp-type';
      typeEl.textContent = info.type || 'unknown';

      const healthEl = document.createElement('span');
      healthEl.className = 'badge badge--' + (info.healthy ? 'accent' : 'error');
      healthEl.textContent = info.healthy ? 'Healthy' : 'Unhealthy';

      row.appendChild(slotEl);
      row.appendChild(typeEl);
      row.appendChild(healthEl);
      table.appendChild(row);
    }
  });

  panel.appendChild(table);
  return panel;
}

// -- Setup Helpers ----------------------------------------------------------

function createSetupPanel(title, subtitle) {
  const panel = document.createElement('div');
  panel.className = 'setup-panel card';

  const header = document.createElement('div');
  header.className = 'setup-panel__header';

  const h3 = document.createElement('h3');
  h3.className = 'setup-panel__title';
  h3.textContent = title;
  header.appendChild(h3);

  if (subtitle) {
    const sub = document.createElement('p');
    sub.className = 'setup-panel__subtitle';
    sub.textContent = subtitle;
    header.appendChild(sub);
  }

  panel.appendChild(header);
  return panel;
}

function createFormRow(label, input) {
  const row = document.createElement('div');
  row.className = 'setup-form-row';

  const lbl = document.createElement('label');
  lbl.className = 'setup-form-label';
  lbl.textContent = label;

  row.appendChild(lbl);
  row.appendChild(input);
  return row;
}

function createRadioOption(groupName, value, label, checked) {
  const wrapper = document.createElement('label');
  wrapper.className = 'setup-radio';

  const input = document.createElement('input');
  input.type = 'radio';
  input.name = groupName;
  input.value = value;
  if (checked) input.checked = true;

  const text = document.createElement('span');
  text.textContent = label;

  wrapper.appendChild(input);
  wrapper.appendChild(text);
  return wrapper;
}
