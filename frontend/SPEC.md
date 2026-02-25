# Frontend Demo — Specification & Functional Requirements

## 1. Overview

Single-page application showcasing the Technical Documentation RAG system through 5 interactive views. Self-contained HTML/CSS/JS with no build step. Operates in two modes: demo (mock data derived from real system metrics) and live (connects to FastAPI gateway at localhost:8080).

**Target audience:** Hiring managers and technical reviewers evaluating the RAG portfolio for Swiss ML Engineer roles.

**Constraints:** No framework, no build tooling, no npm. Single external dependency (Chart.js 4.4.7 via CDN). Three Google Fonts loaded via CDN (Syne, Outfit, Fira Code).


## 2. Architecture

### 2.1 File Structure

```
frontend/
  index.html              # SPA shell: header, nav, 5 <section> elements, footer
  css/
    variables.css          # Design tokens (colors, typography, spacing)
    layout.css             # Grid system, nav, page visibility, responsive, scrollbar
    components.css         # Reusable component styles (cards, badges, tables, etc.)
    visualizations.css     # Chart containers, architecture diagram CSS
    pages.css              # Page-specific styles for all 5 views
  js/
    state.js               # Observable state store + hash router
    data.js                # All mock data (real values from training reports)
    api.js                 # Dual-mode fetch client (demo/live)
    components.js          # 10 DOM render functions
    charts.js              # 7 Chart.js factory functions + instance management
    pages.js               # 5 page-level renderers
    app.js                 # Initialization, event wiring, mode toggle
```

13 files, ~4,581 lines total.

### 2.2 Module Dependency Graph

```
app.js
  ├── state.js        (AppState, navigateTo)
  ├── api.js          (checkConnection)
  ├── charts.js       (destroyAllCharts)
  └── pages.js        (5 render functions)
        ├── state.js
        ├── data.js   (MOCK_DATA)
        ├── api.js    (submitQuery, compareConfigs)
        ├── components.js (10 render functions)
        └── charts.js     (7 chart factories)
```

### 2.3 State Management

Observable store pattern (IIFE, no class). State keys:

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `mode` | `'demo' \| 'live'` | `'demo'` | API dispatch mode |
| `activePage` | string | `'home'` | Current visible page |
| `isLoading` | boolean | `false` | Submit button disabled state |
| `currentQuery` | string | `''` | Current query text |
| `currentStrategy` | string | `'balanced'` | Selected strategy |
| `queryResult` | object \| null | `null` | Last query response |
| `selectedDocument` | object \| null | `null` | Selected corpus document |
| `selectedConfig` | object \| null | `null` | Selected config file |
| `compareResults` | object \| null | `null` | Config comparison response |
| `selectedTrainingQuery` | object \| null | `null` | Selected training query |
| `connectionStatus` | `'connected' \| 'disconnected'` | `'disconnected'` | Live API reachability |

API: `AppState.get(key)`, `AppState.set(key, value)`, `AppState.on(key, callback)` (returns unsubscribe fn), `AppState.off(key, callback)`.

### 2.4 Routing

Hash-based. Valid routes: `#home`, `#query`, `#corpus`, `#architecture`, `#performance`. Invalid hashes fall back to `#home`. On `hashchange`, the router sets `AppState.activePage`, which triggers section visibility toggling and nav tab highlighting.

### 2.5 API Client

`dispatch(endpoint, payload)` checks `AppState.mode`:
- **Demo:** Returns mock data after 200-400ms random delay.
- **Live:** POSTs to `http://localhost:8080/api/v1/{endpoint}`. On failure, logs warning and falls back to demo data.

Query classification heuristic (demo mode): text containing "calculate"/"how many" → agent mock; "compare"/"versus"/" vs "/"analyze"/"implications", length > 80, or compound queries (" and " + length > 50) → complex mock; otherwise → simple mock.


## 3. Design System

### 3.1 Visual Language

Engineering instrument aesthetic: dark, precise, data-dense. Swiss typographic grid. Sharp corners (2px radius). No decorative animations. 150ms transitions on hover states only.

### 3.2 Color Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#0a0a0a` | Page background |
| `--bg-surface` | `#141414` | Cards, panels |
| `--bg-elevated` | `#1e1e1e` | Hover states |
| `--bg-inset` | `#0f0f0f` | Inputs, code blocks |
| `--border` | `#2a2a2a` | Default borders |
| `--border-active` | `#3a3a3a` | Focus/hover borders |
| `--text-primary` | `#e8e8e8` | Headings |
| `--text-secondary` | `#999` | Body text |
| `--text-muted` | `#555` | Labels, placeholders |
| `--accent` | `#00d46a` | Signal green — primary accent |
| `--accent-dim` | `#00d46a22` | Accent backgrounds |
| `--accent-hover` | `#33ff8c` | Accent hover state |
| `--warning` | `#f59e0b` | Medium complexity, warnings |
| `--error` | `#ef4444` | High complexity, errors |
| `--info` | `#60a5fa` | Info badges |

### 3.3 Typography

- **Display:** Syne (700/600) — headings, page titles
- **Body:** Outfit (400/500) — paragraph text, labels
- **Mono:** Fira Code (400/500) — metrics, data, code

### 3.4 Layout

12-column CSS grid, 24px gutter, 1280px max-width. Responsive breakpoint at 768px collapses to single column.

### 3.5 Reusable Components (10)

| Component | Function | Behavior |
|-----------|----------|----------|
| Confidence Gauge | `renderConfidenceGauge(container, value)` | Horizontal bar, 0-1 scale, accent fill, mono % label |
| Badge | `renderBadge(text, variant)` | Pill span, returns element (not appended). Variants: accent, warning, error, info, muted |
| Metric Card | `renderMetricCard(container, label, value, unit)` | Large mono number with label, surface background |
| Data Table | `renderDataTable(container, headers, rows, options)` | Alternating rows, optional `onRowClick` callback |
| Source Card | `renderSourceCard(container, source, index)` | Expandable card: title, score bar, snippet, file/method badges |
| Reasoning Step | `renderReasoningStep(container, step)` | Timeline node with colored left border per type (THOUGHT/ACTION/OBSERVATION/FINAL_ANSWER) |
| Tree Node | `renderTreeNode(container, node, depth)` | Collapsible tree with lazy child rendering, depth indentation |
| Config Block | `renderConfigBlock(container, name, features)` | Key-value display with syntax-highlighted keys |
| Pipeline Timing | `renderPipelineTiming(container, timing)` | Stacked horizontal bar: analysis/retrieval/generation segments |
| Cost Breakdown | `renderCostBreakdown(container, cost)` | Compact table: model cost, retrieval cost, total ($0.0000 format) |

### 3.6 Chart Factories (7)

All tracked in a `Map<canvasId, Chart>` for cleanup on page switch via `destroyAllCharts()`.

| Chart | Function | Usage |
|-------|----------|-------|
| Radar | `createRadarChart(containerId, labels, datasets)` | 5-axis view scores, 0-1 scale, green fill |
| Doughnut | `createDoughnutChart(containerId, labels, data, colors)` | Corpus categories, 65% cutout |
| Horizontal Bar | `createHorizontalBarChart(containerId, labels, data)` | Feature importance, subcategory counts |
| Grouped Bar | `createGroupedBarChart(containerId, labels, datasets)` | Fusion method comparison (val vs test) |
| Stacked Bar | `createStackedBarChart(containerId, labels, datasets)` | Pipeline timing segments |
| Cost Comparison | `createCostComparisonChart(containerId, strategies, costs)` | 3 strategies, color-coded (green/amber/red) |
| Destroy All | `destroyAllCharts()` | Teardown all tracked instances |


## 4. Functional Requirements by Page

### 4.1 Landing Page (`#home`)

**FR-HOME-1:** Display hero section with title "Technical Documentation RAG", subtitle "RISC-V Knowledge System", and one-paragraph system description.

**FR-HOME-2:** Show 3 capability cards in a grid row:
- Epic 1 "Multi-Model Intelligence" (accent badge) — 98% accuracy, 40% cost reduction, 5-view analysis
- Epic 2 "Advanced Retrieval" (info badge) — Hybrid search, 4 fusion strategies, neural reranking
- Epic 5 "Agent-Based RAG" (warning badge) — ReAct reasoning, 3 tools, working memory

**FR-HOME-3:** Display stats bar with 5 values from `MOCK_DATA.systemStats`: 73 Documents, 679 Training Queries, 23 Configurations, 30+ Components, 2,700 Tests.

**FR-HOME-4:** Show tech stack badges: Python, FastAPI, PyTorch, FAISS, sentence-transformers, Pydantic, Chart.js, LangChain, MLflow, Weaviate.

**FR-HOME-5:** "Try a Query" CTA button navigates to `#query`.

### 4.2 Query Demo (`#query`)

**FR-QUERY-1:** Two-column layout. Left panel (4 cols): textarea, strategy selector, submit button, example queries, mode indicator. Right panel (8 cols): results or empty state.

**FR-QUERY-2:** Strategy selector is a 3-option segmented radio control: Cost Optimized, Balanced (default), Quality First.

**FR-QUERY-3:** 10 example queries displayed as clickable rows with type badges:
- 4 simple (accent), 2 medium (warning), 2 complex (error), 2 agent (error)
- Clicking an example fills the textarea and auto-submits.

**FR-QUERY-4:** Submit button calls `submitQuery(text, strategy)`. While loading, button shows "Processing..." and is disabled.

**FR-QUERY-5:** On result, right panel renders in order:
1. Pipeline timing bar (analysis/retrieval/generation segments in ms)
2. Answer card with text and confidence gauge
3. Complexity radar chart (5 axes: Technical, Linguistic, Semantic, Computational, Task) with complexity badge and overall % score
4. Retrieved sources as expandable cards with score bars and method badges
5. Cost analysis table with strategy and model badges
6. Reasoning trace (only if `result.reasoningSteps` exists) — vertical timeline with typed steps

**FR-QUERY-6:** Three distinct result profiles in demo mode:
- **Simple query:** 4 sources, no reasoning trace, cost ~$0.0003, local model
- **Complex query:** 5 sources, no reasoning trace, cost ~$0.0475, GPT-4
- **Agent query:** 1 source, 8-step reasoning trace (THOUGHT→ACTION→OBSERVATION→THOUGHT→ACTION→OBSERVATION→THOUGHT→FINAL_ANSWER), cost ~$0.0036, Mistral

### 4.3 Corpus Explorer (`#corpus`)

**FR-CORPUS-1:** Page header shows total document count (73) and category count (3).

**FR-CORPUS-2:** Two charts in a grid row:
- Left: Doughnut chart showing category distribution (Core Specs 8, Implementation 10, Research 55)
- Right: Horizontal bar chart showing all subcategories sorted by document count descending

**FR-CORPUS-3:** Below the doughnut chart, 3 legend items with colored dots showing category name, count, and percentage.

**FR-CORPUS-4:** Collapsible document tree mirroring the real corpus directory structure:
- Top level: 3 categories with counts
- Mid level: subcategories with counts (e.g., "Official (2)", "Standards (3)")
- Leaf level: actual PDF filenames with inline metadata (title, size)

**FR-CORPUS-5:** Clicking a leaf document populates a metadata panel below the tree with: Title, File, Category, Path, Size.

### 4.4 Architecture (`#architecture`)

**FR-ARCH-1:** CSS grid system diagram with 12 service boxes across 5 rows:
- Row 1: Client (centered)
- Row 2: API Gateway :8080 (centered)
- Row 3: Query Analyzer :8082, Retriever :8083, Generator :8081
- Row 4: FAISS Index, BM25 Index, Analytics :8085, Cache :8084
- Row 5: Embedder, Fusion, Reranker

Dashed connector lines between rows.

**FR-ARCH-2:** Clicking a service box highlights it (solid accent border) and shows a detail panel with: service name, port, description, and component badges. Clicking the same box again hides the detail.

**FR-ARCH-3:** Component registry as a collapsible tree with categories:
- Top level: Processors, Embedders, Retrievers, Generators, Query Processors
- Nested: Sub-Components → Query Analyzers, LLM Adapters, Fusion Strategies, Rerankers, Tools, Memory
- Counts shown in parentheses. Leaf nodes show type name and class metadata.

**FR-ARCH-4:** Config viewer with dropdown of 23 configuration files. Selecting a config displays: name, description, and feature list via `renderConfigBlock`. First config shown by default.

### 4.5 Performance (`#performance`)

**FR-PERF-1:** Hero metric: "98.04%" (from `val_accuracy * 100`) with subtitle "Classification Accuracy (Validation)".

**FR-PERF-2:** 6 metric cards in a 2x3 grid:
- Validation: MAE (0.043), R² (0.945), Accuracy (98.04%)
- Test: MAE (0.042), R² (0.938), Accuracy (95.10%)

**FR-PERF-3:** Feature importance horizontal bar chart with real weights sorted descending: Linguistic (32.35%), Technical (25.82%), Semantic (15.93%), Task (15.17%), Computational (10.73%).

**FR-PERF-4:** Fusion method comparison grouped bar chart: Weighted Average vs Ensemble across 6 metrics (Accuracy Val/Test, MAE Val/Test, R² Val/Test).

**FR-PERF-5:** Training dataset explorer table with 20 sample queries (from 679 total). Columns: Query (truncated to 60 chars), Complexity badge, Confidence, Relevance. Clicking a row reveals a radar chart below showing that query's 5 view scores.

**FR-PERF-6:** Cost strategy comparison chart: 3 bars for Cost Optimized ($0.0003), Balanced ($0.0036), Quality First ($0.0475). Color-coded green/amber/red. "200x cost difference" annotation.

**FR-PERF-7:** Config comparison tool: textarea (default: "Explain RISC-V privilege levels") + Compare button. On submit, shows 3 side-by-side cards with: config name, model badge, confidence gauge, top score, timing, cost, answer preview (truncated), fusion badge, reranker badge.


## 5. Mock Data Provenance

All mock data in `js/data.js` is derived from real project files, not invented.

| Data | Source File | Key Values |
|------|-------------|------------|
| Model metrics | `models/epic1/epic1_complete_training_report_20250810_183906.json` | val_accuracy=0.9804, val_mae=0.0428, val_r2=0.9451 |
| Feature importance | Same file, `ensemble.feature_importance` | linguistic=0.3235, technical=0.2582, ... |
| Fusion comparison | Same file | weighted_average vs ensemble on 6 metrics |
| View weights | `models/epic1/fusion/weighted_average_fusion.json` | All ~0.2000 (nearly uniform) |
| Training queries | `data/training/epic1_training_dataset_679_with_domain_scores.json` | 20 sampled: 7 simple, 7 medium, 6 complex |
| Corpus structure | `data/riscv_corpus/` directory + `metadata/download-log.json` | 73 PDFs: 8 Core Specs, 10 Implementation, 55 Research |
| Config list | `config/*.yaml` (23 files) | Names and descriptions |
| Component registry | `src/core/component_factory.py` type mappings | Processors, embedders, retrievers, generators, etc. |
| Demo queries | `demo.py` DEMO_QUERIES + CONFIG_COMPARISON | Patterns for example queries |


## 6. Non-Functional Requirements

**NFR-1:** Opens directly via `file://` protocol (no server required for demo mode).

**NFR-2:** Works served via `python3 -m http.server` (no build step).

**NFR-3:** Responsive at 768px breakpoint: single-column layout, stacked elements.

**NFR-4:** No animations (user preference). Transitions limited to 150ms hover states.

**NFR-5:** Dark scrollbar styling (WebKit). Text selection uses accent color.

**NFR-6:** Disabled buttons show 0.5 opacity with `not-allowed` cursor.

**NFR-7:** All DOM construction via `document.createElement` (no innerHTML for structure).

**NFR-8:** Chart instances tracked and destroyed on page transitions to prevent memory leaks.

**NFR-9:** Live mode failure gracefully falls back to demo data with console warning.

**NFR-10:** All JS files pass `node --check` syntax validation.
