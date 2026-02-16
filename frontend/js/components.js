// ---------------------------------------------------------------------------
// components.js -- DOM render functions for the Technical RAG System UI
// ---------------------------------------------------------------------------
// All functions build DOM elements via document.createElement.
// innerHTML is used only for text content, never for structural markup.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// 1. Confidence Gauge
// ---------------------------------------------------------------------------

/**
 * Render a horizontal bar gauge showing a confidence value 0-1.
 * @param {HTMLElement} container - Parent element to append into.
 * @param {number} value - Confidence value between 0 and 1.
 * @returns {HTMLElement} The gauge wrapper element.
 */
export function renderConfidenceGauge(container, value) {
  const clamped = Math.max(0, Math.min(1, value));

  const wrapper = document.createElement('div');
  wrapper.className = 'gauge';

  const track = document.createElement('div');
  track.className = 'gauge__track';

  const fill = document.createElement('div');
  fill.className = 'gauge__fill';
  fill.style.width = (clamped * 100) + '%';

  track.appendChild(fill);

  const label = document.createElement('span');
  label.className = 'gauge__value';
  label.textContent = (clamped * 100).toFixed(1) + '%';

  wrapper.appendChild(track);
  wrapper.appendChild(label);
  container.appendChild(wrapper);

  return wrapper;
}

// ---------------------------------------------------------------------------
// 2. Badge
// ---------------------------------------------------------------------------

/**
 * Create a pill badge span.
 * @param {string} text - Badge label.
 * @param {string} [variant='muted'] - One of: accent, warning, error, info, muted.
 * @returns {HTMLSpanElement} The badge element (not appended to DOM).
 */
export function renderBadge(text, variant = 'muted') {
  const span = document.createElement('span');
  span.className = 'badge badge--' + variant;
  span.textContent = text;
  return span;
}

// ---------------------------------------------------------------------------
// 3. Metric Card
// ---------------------------------------------------------------------------

/**
 * Render a metric display card with a large mono number.
 * @param {HTMLElement} container - Parent element.
 * @param {string} label - Descriptive label below the value.
 * @param {string|number} value - The primary metric value.
 * @param {string} [unit=''] - Unit suffix shown next to the value.
 * @returns {HTMLElement} The card element.
 */
export function renderMetricCard(container, label, value, unit = '') {
  const card = document.createElement('div');
  card.className = 'card metric-card';

  const valueRow = document.createElement('div');
  valueRow.className = 'metric-card__value-row';

  const valueEl = document.createElement('span');
  valueEl.className = 'metric-card__value';
  valueEl.textContent = String(value);

  valueRow.appendChild(valueEl);

  if (unit) {
    const unitEl = document.createElement('span');
    unitEl.className = 'metric-card__unit';
    unitEl.textContent = unit;
    valueRow.appendChild(unitEl);
  }

  const labelEl = document.createElement('span');
  labelEl.className = 'metric-card__label';
  labelEl.textContent = label;

  card.appendChild(valueRow);
  card.appendChild(labelEl);
  container.appendChild(card);

  return card;
}

// ---------------------------------------------------------------------------
// 4. Data Table
// ---------------------------------------------------------------------------

/**
 * Render a data table with optional row-click callback.
 * @param {HTMLElement} container - Parent element.
 * @param {string[]} headers - Column header labels.
 * @param {Array<Array<string|number>>} rows - 2D array of cell values.
 * @param {Object} [options={}] - Options object.
 * @param {Function} [options.onRowClick] - Callback receiving (row, index) on click.
 * @returns {HTMLTableElement} The table element.
 */
export function renderDataTable(container, headers, rows, options = {}) {
  const table = document.createElement('table');
  table.className = 'data-table';
  if (options.onRowClick) {
    table.classList.add('data-table--clickable');
  }

  // Header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  for (const h of headers) {
    const th = document.createElement('th');
    th.textContent = h;
    headerRow.appendChild(th);
  }
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement('tbody');
  rows.forEach((row, rowIdx) => {
    const tr = document.createElement('tr');
    for (const cell of row) {
      const td = document.createElement('td');
      if (cell instanceof HTMLElement) {
        td.appendChild(cell);
      } else {
        td.textContent = String(cell);
      }
      tr.appendChild(td);
    }
    if (options.onRowClick) {
      tr.addEventListener('click', () => options.onRowClick(row, rowIdx));
    }
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.appendChild(table);
  return table;
}

// ---------------------------------------------------------------------------
// 5. Source Card
// ---------------------------------------------------------------------------

/**
 * Render an expandable source card for a retrieval result.
 * @param {HTMLElement} container - Parent element.
 * @param {Object} source - Source object with title, score, snippet, file, method.
 * @param {number} index - 1-based index number.
 * @returns {HTMLElement} The source card element.
 */
export function renderSourceCard(container, source, index) {
  const card = document.createElement('div');
  card.className = 'card source-card';

  // Header row: index + title + score
  const header = document.createElement('div');
  header.className = 'source-card__header';

  const indexEl = document.createElement('span');
  indexEl.className = 'source-card__index';
  indexEl.textContent = '#' + index;

  const titleEl = document.createElement('span');
  titleEl.className = 'source-card__title';
  titleEl.textContent = source.title || 'Untitled';

  header.appendChild(indexEl);
  header.appendChild(titleEl);

  // Score bar
  const scoreRow = document.createElement('div');
  scoreRow.className = 'source-card__score-row';

  const scoreLabel = document.createElement('span');
  scoreLabel.className = 'source-card__score-label';
  scoreLabel.textContent = 'Score';

  const scoreGauge = document.createElement('div');
  scoreGauge.className = 'gauge';

  const scoreTrack = document.createElement('div');
  scoreTrack.className = 'gauge__track';

  const scoreFill = document.createElement('div');
  scoreFill.className = 'gauge__fill';
  const clampedScore = Math.max(0, Math.min(1, source.score || 0));
  scoreFill.style.width = (clampedScore * 100) + '%';

  scoreTrack.appendChild(scoreFill);

  const scoreValue = document.createElement('span');
  scoreValue.className = 'gauge__value';
  scoreValue.textContent = clampedScore.toFixed(2);

  scoreGauge.appendChild(scoreTrack);
  scoreGauge.appendChild(scoreValue);

  scoreRow.appendChild(scoreLabel);
  scoreRow.appendChild(scoreGauge);

  // Snippet (truncated in collapsed state)
  const snippetEl = document.createElement('div');
  snippetEl.className = 'source-card__snippet';
  const truncatedLength = 150;
  const fullText = source.snippet || '';
  const isTruncatable = fullText.length > truncatedLength;
  snippetEl.textContent = isTruncatable
    ? fullText.substring(0, truncatedLength) + '...'
    : fullText;

  // Badges row
  const badgeRow = document.createElement('div');
  badgeRow.className = 'source-card__badges';
  if (source.file) {
    badgeRow.appendChild(renderBadge(source.file, 'muted'));
  }
  if (source.method) {
    badgeRow.appendChild(renderBadge(source.method, 'accent'));
  }

  // Expanded content (hidden by default)
  const expandedContent = document.createElement('div');
  expandedContent.className = 'source-card__expanded';
  expandedContent.style.display = 'none';

  const fullSnippetEl = document.createElement('div');
  fullSnippetEl.className = 'source-card__full-snippet';
  fullSnippetEl.textContent = fullText;
  expandedContent.appendChild(fullSnippetEl);

  // Click to expand/collapse
  let expanded = false;
  header.style.cursor = 'pointer';
  header.addEventListener('click', () => {
    expanded = !expanded;
    expandedContent.style.display = expanded ? 'block' : 'none';
    snippetEl.style.display = expanded ? 'none' : 'block';
    card.classList.toggle('source-card--expanded', expanded);
  });

  card.appendChild(header);
  card.appendChild(scoreRow);
  card.appendChild(snippetEl);
  card.appendChild(expandedContent);
  card.appendChild(badgeRow);
  container.appendChild(card);

  return card;
}

// ---------------------------------------------------------------------------
// 6. Reasoning Step
// ---------------------------------------------------------------------------

/**
 * Render a timeline node for agent reasoning.
 * @param {HTMLElement} container - Parent element.
 * @param {Object} step - Step object with type, content, tool, input.
 * @returns {HTMLElement} The step element.
 */
export function renderReasoningStep(container, step) {
  const typeClass = (step.type || 'thought').toLowerCase();
  const el = document.createElement('div');
  el.className = 'reasoning-step reasoning-step--' + typeClass;

  // Type label
  const typeLabel = document.createElement('span');
  typeLabel.className = 'reasoning-step__type';
  typeLabel.textContent = step.type || 'THOUGHT';

  // Content
  const contentEl = document.createElement('div');
  contentEl.className = 'reasoning-step__content';
  contentEl.textContent = step.content || '';

  el.appendChild(typeLabel);
  el.appendChild(contentEl);

  // Tool sub-block for ACTION steps
  if (step.type === 'ACTION' && (step.tool || step.input)) {
    const toolBlock = document.createElement('div');
    toolBlock.className = 'reasoning-step__tool-block';

    if (step.tool) {
      const toolName = document.createElement('span');
      toolName.className = 'reasoning-step__tool-name';
      toolName.textContent = step.tool;
      toolBlock.appendChild(toolName);
    }

    if (step.input) {
      const toolInput = document.createElement('code');
      toolInput.className = 'reasoning-step__tool-input';
      toolInput.textContent = step.input;
      toolBlock.appendChild(toolInput);
    }

    el.appendChild(toolBlock);
  }

  container.appendChild(el);
  return el;
}

// ---------------------------------------------------------------------------
// 7. Tree Node
// ---------------------------------------------------------------------------

/**
 * Render a collapsible tree item.
 * @param {HTMLElement} container - Parent element.
 * @param {Object} node - Node with name, children (array), metadata (object).
 * @param {number} [depth=0] - Indentation depth.
 * @returns {HTMLElement} The tree node element.
 */
export function renderTreeNode(container, node, depth = 0) {
  const wrapper = document.createElement('div');
  wrapper.className = 'tree-node';
  wrapper.style.paddingLeft = (depth * 20) + 'px';

  const row = document.createElement('div');
  row.className = 'tree-node__row';

  const hasChildren = node.children && node.children.length > 0;

  if (hasChildren) {
    const toggle = document.createElement('button');
    toggle.className = 'tree-node__toggle';
    toggle.textContent = '\u25B8'; // ▸
    toggle.setAttribute('aria-label', 'Toggle ' + node.name);

    const childContainer = document.createElement('div');
    childContainer.className = 'tree-node__children';
    childContainer.style.display = 'none';

    let childrenRendered = false;
    let expanded = false;

    toggle.addEventListener('click', () => {
      expanded = !expanded;
      toggle.textContent = expanded ? '\u25BE' : '\u25B8'; // ▾ / ▸
      childContainer.style.display = expanded ? 'block' : 'none';

      // Lazy-render children on first expand
      if (expanded && !childrenRendered) {
        for (const child of node.children) {
          renderTreeNode(childContainer, child, depth + 1);
        }
        childrenRendered = true;
      }
    });

    row.appendChild(toggle);

    const nameEl = document.createElement('span');
    nameEl.className = 'tree-node__name';
    nameEl.textContent = node.name || '';
    row.appendChild(nameEl);

    wrapper.appendChild(row);
    wrapper.appendChild(childContainer);
  } else {
    // Leaf node
    const bullet = document.createElement('span');
    bullet.className = 'tree-node__bullet';
    bullet.textContent = '\u2022'; // bullet

    const nameEl = document.createElement('span');
    nameEl.className = 'tree-node__name';
    nameEl.textContent = node.name || '';
    row.appendChild(bullet);
    row.appendChild(nameEl);

    // Inline metadata for leaf nodes
    if (node.metadata) {
      const meta = document.createElement('span');
      meta.className = 'tree-node__metadata';
      const entries = Object.entries(node.metadata);
      meta.textContent = entries.map(([k, v]) => k + ': ' + v).join(' | ');
      row.appendChild(meta);
    }

    wrapper.appendChild(row);
  }

  container.appendChild(wrapper);
  return wrapper;
}

// ---------------------------------------------------------------------------
// 8. Config Block
// ---------------------------------------------------------------------------

/**
 * Render a formatted config display.
 * @param {HTMLElement} container - Parent element.
 * @param {string} configName - Configuration name/title.
 * @param {Object} features - Key-value pairs to display.
 * @returns {HTMLElement} The config block element.
 */
export function renderConfigBlock(container, configName, features) {
  const block = document.createElement('div');
  block.className = 'config-block';

  const header = document.createElement('div');
  header.className = 'config-block__header';
  header.textContent = configName;
  block.appendChild(header);

  const list = document.createElement('div');
  list.className = 'config-block__list';

  // Color classification for keys
  const componentTypes = ['processor', 'embedder', 'retriever', 'generator', 'query_processor', 'reranker', 'fusion', 'index'];
  const modelNames = ['model', 'adapter', 'llm', 'encoder', 'embedding'];
  const strategyNames = ['strategy', 'routing', 'fallback', 'mode'];

  for (const [key, value] of Object.entries(features)) {
    const row = document.createElement('div');
    row.className = 'config-block__row';

    const keyEl = document.createElement('span');
    keyEl.className = 'config-block__key';
    keyEl.textContent = key;

    // Determine key color class
    const lowerKey = key.toLowerCase();
    if (componentTypes.some(t => lowerKey.includes(t))) {
      keyEl.classList.add('config-block__key--component');
    } else if (modelNames.some(t => lowerKey.includes(t))) {
      keyEl.classList.add('config-block__key--model');
    } else if (strategyNames.some(t => lowerKey.includes(t))) {
      keyEl.classList.add('config-block__key--strategy');
    }

    const separator = document.createElement('span');
    separator.className = 'config-block__separator';
    separator.textContent = ':';

    const valueEl = document.createElement('span');
    valueEl.className = 'config-block__value';
    valueEl.textContent = String(value);

    row.appendChild(keyEl);
    row.appendChild(separator);
    row.appendChild(valueEl);
    list.appendChild(row);
  }

  block.appendChild(list);
  container.appendChild(block);

  return block;
}

// ---------------------------------------------------------------------------
// 9. Pipeline Timing
// ---------------------------------------------------------------------------

/**
 * Render a stacked horizontal bar for pipeline phase timings.
 * @param {HTMLElement} container - Parent element.
 * @param {Object} timing - Object with analysis, retrieval, generation (ms).
 * @returns {HTMLElement} The pipeline bar element.
 */
export function renderPipelineTiming(container, timing) {
  const wrapper = document.createElement('div');
  wrapper.className = 'pipeline-timing';

  const analysis = timing.analysis || 0;
  const retrieval = timing.retrieval || 0;
  const generation = timing.generation || 0;
  const total = analysis + retrieval + generation;

  const bar = document.createElement('div');
  bar.className = 'pipeline-bar';

  const segments = [
    { label: 'Analysis', value: analysis, cls: 'pipeline-bar__segment--analysis' },
    { label: 'Retrieval', value: retrieval, cls: 'pipeline-bar__segment--retrieval' },
    { label: 'Generation', value: generation, cls: 'pipeline-bar__segment--generation' },
  ];

  for (const seg of segments) {
    if (seg.value <= 0) continue;
    const segEl = document.createElement('div');
    segEl.className = 'pipeline-bar__segment ' + seg.cls;
    segEl.style.width = ((seg.value / total) * 100) + '%';
    segEl.title = seg.label + ': ' + seg.value + 'ms';

    const segLabel = document.createElement('span');
    segLabel.className = 'pipeline-bar__label';
    segLabel.textContent = seg.value + 'ms';
    segEl.appendChild(segLabel);

    bar.appendChild(segEl);
  }

  const totalLabel = document.createElement('span');
  totalLabel.className = 'pipeline-timing__total';
  totalLabel.textContent = total + 'ms';

  wrapper.appendChild(bar);
  wrapper.appendChild(totalLabel);
  container.appendChild(wrapper);

  return wrapper;
}

// ---------------------------------------------------------------------------
// 10. Cost Breakdown
// ---------------------------------------------------------------------------

/**
 * Render a cost breakdown table.
 * @param {HTMLElement} container - Parent element.
 * @param {Object} cost - Cost object with model_cost, retrieval_cost, total.
 *   Optional: model (string), tokens_in (number), tokens_out (number).
 * @returns {HTMLElement} The cost table element.
 */
export function renderCostBreakdown(container, cost) {
  const fmt = (v) => {
    if (v == null || v === undefined) return 'N/A';
    return '$' + Number(v).toFixed(4);
  };

  const model = cost.model || 'N/A';
  const tokensIn = cost.tokens_in != null ? String(cost.tokens_in) : 'N/A';
  const tokensOut = cost.tokens_out != null ? String(cost.tokens_out) : 'N/A';

  const headers = ['Metric', 'Value'];
  const rows = [
    ['Model', model],
    ['Tokens In', tokensIn],
    ['Tokens Out', tokensOut],
    ['Model Cost', fmt(cost.model_cost)],
    ['Retrieval Cost', fmt(cost.retrieval_cost)],
    ['Total Cost', fmt(cost.total)],
  ];

  const table = renderDataTable(container, headers, rows);
  table.classList.add('cost-table');

  return table;
}
