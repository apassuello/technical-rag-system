# Frontend SPA Audit Report

**Branch:** `demo-frontend` vs `plan-b`
**Date:** 2026-02-16
**Scope:** 12 files, 4,216 lines in `frontend/`
**Spec:** `frontend/SPEC.md`

---

## Agent 1: Functional Completeness + Component Contracts

### Functional Completeness — All 27 FR Requirements

#### Landing Page (#home)

**FR-HOME-1: Hero Section** — PASS
- Location: `pages.js:50-72`
- Title "Technical Documentation RAG" (line 56), subtitle "RISC-V Knowledge System" (line 60), one-paragraph description (lines 64-67)

**FR-HOME-2: Capability Cards** — PASS
- Location: `pages.js:77-156`
- Three cards: Epic 1 "Multi-Model Intelligence" accent badge (lines 78-90), Epic 2 "Advanced Retrieval" info badge (lines 92-105), Epic 5 "Agent-Based RAG" warning badge (lines 107-118)
- Metrics match spec: 98% accuracy, 40% cost reduction, 5-view analysis; Hybrid search, 4 fusion strategies, Neural reranking; ReAct reasoning, 3 tools, Working memory

**FR-HOME-3: Stats Bar** — PASS
- Location: `pages.js:161-193`
- All 5 values from `MOCK_DATA.systemStats`: 73 Documents (line 165), 679 Training Queries (line 166), 23 Configurations (line 167), 30+ Components (line 168), 2,700 Tests (line 169)

**FR-HOME-4: Tech Stack Badges** — PASS
- Location: `pages.js:197-218`
- All 10 technologies: Python, FastAPI, PyTorch, FAISS, sentence-transformers, Pydantic, Chart.js, LangChain, MLflow, Weaviate (lines 197-200)

**FR-HOME-5: CTA Button** — PASS
- Location: `pages.js:223-233`
- Button "Try a Query →" (line 229), navigates to #query (line 230)

#### Query Demo (#query)

**FR-QUERY-1: Two-Column Layout** — PASS
- Location: `pages.js:253-272`
- Left panel col-4: textarea, strategy selector, submit button (lines 266-269). Right panel col-8: results or empty state (line 272). Mode indicator present (line 269).

**FR-QUERY-2: Strategy Selector** — PASS
- Location: `pages.js:295-322`
- Three options: Cost Optimized, Balanced (default), Quality First (lines 298-302). Balanced default (line 313). Segmented radio control (lines 304-322).

**FR-QUERY-3: Example Queries** — PASS (badge rendering correct per data)
- Location: `pages.js:341-374`
- 10 queries from `MOCK_DATA.exampleQueries` (line 350). Data at `data.js:662-673`: 4 simple (accent), 2 medium (warning), 2 complex (error), 2 agent — agent badges use fallback muted instead of error (see finding #3 below). Clickable rows with type badges (lines 350-371). Auto-submit on click (line 368).

**FR-QUERY-4: Submit Button** — PASS
- Location: `pages.js:324-334`
- Calls submitQuery(text, strategy) (line 333). Loading state subscription (lines 280-286): shows "Processing..." and disables button.

**FR-QUERY-5: Result Rendering** — PASS
- Location: `pages.js:397-494`
- All 6 sections in correct order: (1) Pipeline timing bar (lines 400-403), (2) Answer card with confidence gauge (lines 406-415), (3) Complexity radar chart with badge and overall % score (lines 418-448), (4) Retrieved sources as expandable cards (lines 451-462), (5) Cost analysis table with strategy and model badges (lines 465-475), (6) Reasoning trace only if reasoningSteps exists (lines 478-494).

**FR-QUERY-6: Three Result Profiles** — PASS
- Location: `data.js:544-614`
- Simple (lines 545-563): 4 sources, no reasoning trace, cost ~$0.0003, local model. Complex (lines 566-586): 5 sources, no reasoning trace, cost ~$0.0475, GPT-4. Agent (lines 588-614): 1 source, 8-step reasoning trace (THOUGHT→ACTION→OBSERVATION→THOUGHT→ACTION→OBSERVATION→THOUGHT→FINAL_ANSWER), cost ~$0.0036, Mistral.

#### Corpus Explorer (#corpus)

**FR-CORPUS-1: Page Header** — PASS
- Location: `pages.js:529-547`
- Total document count (73) and category count (3) (lines 540-542)

**FR-CORPUS-2: Two Charts** — PASS
- Location: `pages.js:550-628`
- Left: Doughnut chart category distribution (lines 564-574): Core Specs 8, Implementation 10, Research 55. Right: Horizontal bar chart subcategories sorted descending (lines 610-625). Grid row layout (line 552).

**FR-CORPUS-3: Legend Below Doughnut** — PASS
- Location: `pages.js:577-598`
- 3 legend items with colored dots (lines 581-595), showing category name, count, and percentage (line 591)

**FR-CORPUS-4: Collapsible Document Tree** — PASS
- Location: `pages.js:631-674`
- Three levels: Top 3 categories with counts (lines 644-647), Mid subcategories with counts (lines 653-673), Leaf PDF filenames with metadata (lines 655-662). Uses renderTreeNode component (line 646).

**FR-CORPUS-5: Metadata Panel** — PASS
- Location: `pages.js:676-759`
- Click leaf document populates metadata panel (lines 686-706). Shows: Title, File, Category, Path, Size (lines 735-741).

#### Architecture (#architecture)

**FR-ARCH-1: CSS Grid System Diagram** — PASS
- Location: `pages.js:766-888`
- 12 service boxes (lines 766-779), 5 rows: Row 1 Client centered, Row 2 API Gateway :8080 centered, Row 3 Query Analyzer :8082 / Retriever :8083 / Generator :8081, Row 4 FAISS Index / BM25 Index / Analytics :8085 / Cache :8084, Row 5 Embedder / Fusion / Reranker. Dashed connector lines (lines 833-839).

**FR-ARCH-2: Service Box Interaction** — PASS
- Location: `pages.js:869-880`
- Click highlights box with solid accent border (line 876). Detail panel with service name, port, description, component badges (lines 890-911). Click same box again hides detail (lines 871-875).

**FR-ARCH-3: Component Registry** — PASS
- Location: `pages.js:915-979`
- Collapsible tree: Processors, Embedders, Retrievers, Generators, Query Processors (lines 930-935). Nested Sub-Components: Query Analyzers, LLM Adapters, Fusion Strategies, Rerankers, Tools, Memory (lines 942-949). Counts in parentheses (line 975). Leaf nodes show type name and class metadata (lines 964-971).

**FR-ARCH-4: Config Viewer** — PASS
- Location: `pages.js:982-1043`
- Dropdown of 23 configuration files (lines 997-1004). Displays name, description, feature list via renderConfigBlock (lines 1024-1042). First config shown by default (lines 1017-1019).

#### Performance (#performance)

**FR-PERF-1: Hero Metric** — PASS
- Location: `pages.js:1065-1084`
- "98.04%" from val_accuracy * 100 (line 1076). Subtitle "Classification Accuracy (Validation)" (line 1080).

**FR-PERF-2: 6 Metric Cards** — PASS
- Location: `pages.js:1086-1106`
- 2x3 grid: Validation MAE (0.043), R² (0.945), Accuracy (98.04%); Test MAE (0.042), R² (0.938), Accuracy (95.10%) (lines 1089-1096).

**FR-PERF-3: Feature Importance Chart** — PASS
- Location: `pages.js:1111-1136`
- Horizontal bar chart from `MOCK_DATA.modelMetrics.featureImportance` (line 1125): Linguistic (32.35%), Technical (25.82%), Semantic (15.93%), Task (15.17%), Computational (10.73%).

**FR-PERF-4: Fusion Method Comparison** — PASS
- Location: `pages.js:1140-1174`
- Grouped bar chart: Weighted Average vs Ensemble (lines 1164-1167), 6 metrics: Accuracy Val/Test, MAE Val/Test, R² Val/Test (lines 1158-1162).

**FR-PERF-5: Training Dataset Explorer** — PASS
- Location: `pages.js:1178-1228`
- Table with 20 sample queries from 679 total (line 1186). Columns: Query (truncated to 60 chars), Complexity badge, Confidence, Relevance (lines 1190-1196). Click row reveals radar chart with 5 view scores (lines 1210-1223).

**FR-PERF-6: Cost Strategy Comparison** — PASS
- Location: `pages.js:1232-1256`
- 3 bars: Cost Optimized ($0.0003), Balanced ($0.0036), Quality First ($0.0475) (line 1247). Color-coded green/amber/red. "200x cost difference" annotation (lines 1250-1253).

**FR-PERF-7: Config Comparison Tool** — PASS
- Location: `pages.js:1260-1372`
- Textarea with default "Explain RISC-V privilege levels" (line 1275). Compare button (lines 1278-1285). 3 side-by-side cards: config name + model badge (lines 1316-1322), confidence gauge (lines 1324-1333), top score / timing / cost (lines 1335-1337), answer preview truncated to 160 chars (lines 1339-1342), fusion badge + reranker badge (lines 1344-1348).

### Component Contracts — All 10 Render Functions

All functions in `components.js`.

| # | Function | Lines | Signature | Appends to container? | Returns element? | Status |
|---|----------|-------|-----------|----------------------|-----------------|--------|
| 1 | renderConfidenceGauge | 18-42 | `(container, value)` | Yes (line 39) | Yes (line 41) | PASS |
| 2 | renderBadge | 54-59 | `(text, variant='muted')` | **No** (returns only) | Yes (line 58) | PASS — spec-correct exception |
| 3 | renderMetricCard | 73-102 | `(container, label, value, unit='')` | Yes (line 99) | Yes (line 101) | PASS |
| 4 | renderDataTable | 117-157 | `(container, headers, rows, options={})` | Yes (line 155) | Yes (line 156) | PASS |
| 5 | renderSourceCard | 170-268 | `(container, source, index)` | Yes (line 265) | Yes (line 267) | PASS |
| 6 | renderReasoningStep | 280-322 | `(container, step)` | Yes (line 320) | Yes (line 321) | PASS |
| 7 | renderTreeNode | 335-407 | `(container, node, depth=0)` | Yes (line 405) | Yes (line 406) | PASS |
| 8 | renderConfigBlock | 420-473 | `(container, configName, features)` | Yes (line 470) | Yes (line 472) | PASS (param named `configName` vs spec `name`) |
| 9 | renderPipelineTiming | 485-527 | `(container, timing)` | Yes (line 524) | Yes (line 526) | PASS |
| 10 | renderCostBreakdown | 540-564 | `(container, cost)` | Yes (via renderDataTable, line 560) | Yes (line 563) | PASS |

**Note:** renderConfigBlock uses parameter name `configName` instead of spec's `name`. Functionally equivalent — local variable only.

---

## Agent 2: Chart Lifecycle, State/Routing, API Client, Mock Data

### Chart Lifecycle — PASS

**Instance tracking** (`charts.js:10`):
```javascript
const chartInstances = new Map();
```

**All 7 chart factories register in Map** via `_create()` helper (line 72):
| Factory | Line | Signature |
|---------|------|-----------|
| createRadarChart | 86 | `(containerId, labels, datasets)` |
| createDoughnutChart | 143 | `(containerId, labels, data, colors)` |
| createHorizontalBarChart | 187 | `(containerId, labels, data)` + optional `options` |
| createGroupedBarChart | 259 | `(containerId, labels, datasets)` |
| createStackedBarChart | 304 | `(containerId, labels, datasets)` + optional `options` |
| createCostComparisonChart | 351 | `(containerId, strategies, costs)` |
| destroyAllCharts | 37 | `()` |

**Cleanup on transition** (`app.js:32`):
```javascript
function renderPage(page) {
  destroyAllCharts();  // Called before every page render
```

**Signature extensions:** `createHorizontalBarChart` and `createStackedBarChart` accept optional `options` parameter not in spec. Non-breaking, backward-compatible.

### State/Routing

**AppState keys** (`state.js:6-18`):

| Key | Spec §2.3 | Default | Present |
|-----|-----------|---------|---------|
| `mode` | Yes | `'demo'` | Yes |
| `activePage` | Yes | `'home'` | Yes |
| `isLoading` | Yes | `false` | Yes |
| `queryResult` | Yes | `null` | Yes |
| `compareResults` | Yes | `null` | Yes |
| `connectionStatus` | Yes | `'disconnected'` | Yes |
| `currentQuery` | **No** | `''` | Yes |
| `currentStrategy` | **No** | `'balanced'` | Yes |
| `selectedDocument` | **No** | `null` | Yes |
| `selectedConfig` | **No** | `null` | Yes |
| `selectedTrainingQuery` | **No** | `null` | Yes |

**FINDING: 5 undocumented keys** not in SPEC §2.3. Used internally, work correctly. Documentation gap.

**API** — PASS:
- `get(key)` (line 23)
- `set(key, value)` (line 27) with broadcast to listeners
- `on(key, callback)` (line 35) returns unsubscribe function (line 40)
- `off(key, callback)` (line 43)

**Hash Router** — PASS:
- Valid routes: `['home', 'query', 'corpus', 'architecture', 'performance']` (line 57)
- Invalid hashes fall back to `'home'` (line 61)
- `hashchange` event sets `activePage` (line 88)
- Section visibility toggled (lines 69-75)
- Nav tab highlighting (lines 78-80)

**Page re-rendering** (`app.js:30-43`):
- `alwaysRerender` set: `['query', 'performance']` (line 38)
- Other pages render once and cache via `renderedPages` Set (line 28)

### API Client — PASS

**Query classification heuristic** (`api.js:18-25`):
```javascript
function classifyQuery(text) {
  const lower = text.toLowerCase();
  if (lower.includes('calculate') || lower.includes('how many') || lower.includes('what is'))
    return 'agent';
  if (lower.includes('compare') || lower.includes('versus') || text.length > 100)
    return 'complex';
  return 'simple';
}
```
Matches SPEC §2.5 keywords exactly. (But see cross-check against example queries in Findings section.)

**dispatch() flow** (`api.js:27-51`):
- Checks `AppState.get('mode')` (line 28)
- Demo: returns mock data after 200-400ms delay via `mockLatency()` (lines 14-15, 29-33)
- Live: POST to `http://localhost:8080/api/v1/{endpoint}` (line 37)
- Failure fallback: logs warning, falls back to demo data (lines 44-48)

### Mock Data Fidelity — PASS (all values verified)

**Model metrics** (`data.js:16-23`):
| Metric | Spec §5 | data.js | Line |
|--------|---------|---------|------|
| val_accuracy | 0.9804 | 0.9804 | 17 |
| val_mae | 0.0428 | 0.0428 | 18 |
| val_r2 | 0.9451 | 0.9451 | 19 |

**Feature importance** (`data.js:24-30`):
| Feature | Spec §5 | data.js | Line |
|---------|---------|---------|------|
| linguistic | 0.3235 | 0.3235 | 26 |
| technical | 0.2582 | 0.2582 | 27 |
| semantic | 0.1593 | 0.1593 | 28 |
| task | 0.1517 | 0.1517 | 29 |
| computational | 0.1073 | 0.1073 | 30 |

**System stats** (`data.js:678-684`):
| Stat | Spec §5 | data.js | Line |
|------|---------|---------|------|
| Documents | 73 | 73 | 679 |
| Training Queries | 679 | 679 | 680 |
| Configurations | 23 | 23 | 681 |
| Components | 30+ | 30 | 682 |
| Tests | 2,700 | 2700 | 683 |

**Query mock profiles** (`data.js:544-614`): 3 profiles — simple (4 sources, $0.0003), complex (5 sources, $0.0475), agent (1 source + 8-step reasoning trace, $0.0036). All match FR-QUERY-6.

**Corpus structure** (`data.js:255-437`): `totalDocuments: 73`, 3 categories (Core Specs 8, Implementation 10, Research 55). Matches spec.

**Training queries** (`data.js:86-249`): 20 samples — 7 simple, 7 medium, 6 complex. Matches spec §5 provenance.

---

## Agent 3: CSS/Design, NFR Compliance, Bug Hunt

### CSS/Design Tokens — PASS

**Color tokens** (`variables.css:5-29`):
All 14 spec tokens match SPEC §3.2 exactly:
- `--bg-primary: #0a0a0a`, `--bg-surface: #141414`, `--bg-elevated: #1e1e1e`, `--bg-inset: #0f0f0f`
- `--border: #2a2a2a`, `--border-active: #3a3a3a`
- `--text-primary: #e8e8e8`, `--text-secondary: #999`, `--text-muted: #555`
- `--accent: #00d46a`, `--accent-dim: #00d46a22`
- `--warning: #f59e0b`, `--error: #ef4444`, `--info: #60a5fa`

**FINDING:** Extra token `--accent-hover: #33ff8c` (line 24) not in spec. Used for hover states.

**Typography** (`variables.css:3, 31-34`):
- Display: Syne (600, 700) via CDN
- Body: Outfit (400, 500) via CDN
- Mono: Fira Code (400, 500) via CDN

**Layout grid** (`variables.css:65-68`, `layout.css:24-40`):
- 12-column: `--grid-cols: 12`
- 24px gutter: `--grid-gutter: 24px`
- 1280px max-width: `--grid-max: 1280px`
- 768px responsive breakpoint: `layout.css:200`, `pages.css:143`, `visualizations.css:131`

### NFR Compliance — PASS

**NFR-4: Transitions limited to 150ms** — PASS
`--transition: 150ms ease` (variables.css:72). All 11 transition declarations use `var(--transition)`:
- components.css: lines 12, 177, 364, 381
- layout.css: lines 90, 133
- pages.css: lines 34, 50, 58, 93
- visualizations.css: line 59

**NFR-6: Disabled button styling** — PASS
`pages.css:36`: `.btn:disabled { opacity: 0.5; cursor: not-allowed; pointer-events: none; }`

**NFR-7: No innerHTML for DOM structure** — PASS
All 11 `innerHTML` uses across JS files are for clearing containers only:
- `pages.js`: lines 39, 251, 390, 398, 521, 733, 796, 891, 1025, 1053, 1302 — all `container.innerHTML = ''`
- `components.js:5` comment confirms: "innerHTML is used only for text content, never for structural markup."

All DOM construction uses `document.createElement()`.

**NFR-8: Chart cleanup on transitions** — PASS
`destroyAllCharts()` called at `app.js:32` before every page render. Implementation at `charts.js:37-40` destroys all instances and clears the Map.

### Bug Hunt

**Broken imports / Missing exports** — NONE FOUND
All ES module `export function` declarations in source files match `import { ... } from` in consuming files. (Agent initially flagged missing export block in components.js — FALSE POSITIVE: file uses inline `export function` syntax.)

**Undefined references** — NONE FOUND

**Event listener leaks** — SEE FINDING #1
`AppState.on()` subscriptions in `renderQueryPage()` and `renderPerformancePage()` accumulate without cleanup on re-render.

**DOM elements created but never appended** — NONE FOUND

**CSS class mismatches (JS → CSS)** — NONE FOUND

**Null/undefined access without guards** — NONE FOUND
Consistent `if (!container) return;` pattern used.

**Off-by-one errors** — NONE FOUND

**RAF race condition** — SEE FINDING #5
6 `requestAnimationFrame` callbacks lack container existence guards.

**Inline styles** — SEE FINDING #7
5 places use `style.cssText` or `style.*` instead of CSS classes (`pages.js:427, 1028, 1033, 1320, 1328`).

---

## Cross-Agent Analysis (manual verification)

### Query Heuristic vs Example Queries — FINDING #2

Tracing each example query through `classifyQuery()` (`api.js:18-25`):

| # | Label | data.js type | Query text | classifyQuery result | Match? |
|---|-------|-------------|------------|---------------------|--------|
| 1 | Instruction Formats | simple | "What are the base RISC-V integer instruction formats?" | simple (no keywords, 55 chars) | YES |
| 2 | Memory Model | simple | "How does the RISC-V weak memory ordering model work?" | simple (no keywords, 53 chars) | YES |
| 3 | Extensions | simple | "What standard extensions are available in RISC-V?" | simple (no keywords, 50 chars) | YES |
| 4 | Privilege Levels | simple | "Explain RISC-V privilege levels" | simple (no keywords, 31 chars) | YES |
| 5 | Vector Extension | **medium** | "What **is** the RISC-V vector extension and what operations does it support?" | **agent** (matches "what is") | **NO** |
| 6 | PMP Configuration | **medium** | "How does RISC-V handle privilege levels and memory protection?" | **simple** (no keywords, 62 chars) | **NO** |
| 7 | Security Comparison | complex | "**Compare** RISC-V PMP **versus** ARM TrustZone security models..." | complex (matches "compare") | YES |
| 8 | Vector Processing | **complex** | "Analyze the performance implications of RISC-V vector extension **vs** ARM SVE for ML workloads" | **simple** ("vs" not "versus", 91 chars) | **NO** |
| 9 | Register Calculator | agent | "**How many** registers does RV32I define, and **what is** 2^5?" | agent (matches "how many") | YES |
| 10 | Code Analysis | agent | "Analyze the RISC-V instruction decoder function and **calculate** the number of supported formats" | agent (matches "calculate") | YES |

**3 of 10 mismatches.** Impact: clicking these examples shows one badge type but returns a different mock response profile.

### Missing Agent Badge Variant — FINDING #3

`COMPLEXITY_VARIANT` (`pages.js:241-244`) maps `simple→accent`, `medium→warning`, `complex→error` but lacks `agent→error`. Per FR-QUERY-3, agent badges should be red (error variant). Fallback `|| 'muted'` renders them grey.

---

## Summary of All Findings

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| 1 | **BLOCKING** | Listener leak: `AppState.on()` subscriptions accumulate on every re-render of query and performance pages | `pages.js:275,280,382,1293` + `app.js:38` |
| 2 | **BLOCKING** | Query heuristic misclassifies 3 of 10 example queries (wrong mock response returned) | `api.js:18-25` + `data.js:662-672` |
| 3 | SPEC DEVIATION | Agent badge renders grey (muted) instead of red (error) per FR-QUERY-3 | `pages.js:241-244` |
| 4 | SPEC GAP | 5 AppState keys undocumented in SPEC §2.3 | `state.js:10-16` |
| 5 | MINOR | RAF chart callbacks lack container existence guard | `pages.js:438,572,623,1131,1169,1246` |
| 6 | MINOR | Extra color token `--accent-hover` not in SPEC §3.2 | `variables.css:24` |
| 7 | MINOR | 5 inline `style.cssText` assignments bypass CSS class system | `pages.js:427,1028,1033,1320,1328` |
