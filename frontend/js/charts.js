// ---------------------------------------------------------------------------
// charts.js -- Chart.js wrapper functions for dark-themed RAG visualizations
// ---------------------------------------------------------------------------
// Chart.js 4.x is loaded globally via CDN (window.Chart).

const { Chart } = window;

// -- Tracked instances for cleanup ----------------------------------------

const chartInstances = new Map();

// -- Chart.js global defaults ---------------------------------------------

Chart.defaults.color = '#999';
Chart.defaults.borderColor = '#2a2a2a';
Chart.defaults.font.family = 'Outfit';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.animation = false;

// -- Helpers --------------------------------------------------------------

/**
 * Destroy an existing chart on the given canvas (if any) and remove it from
 * the instance map.
 */
function destroyChart(canvasId) {
  const existing = chartInstances.get(canvasId);
  if (existing) {
    existing.destroy();
    chartInstances.delete(canvasId);
  }
}

/**
 * Destroy every tracked chart instance — call when switching pages.
 */
function destroyAllCharts() {
  chartInstances.forEach((chart) => chart.destroy());
  chartInstances.clear();
}

/**
 * Look for a <canvas> inside the container div.  If none exists, create one
 * with the supplied canvasId.  Returns the canvas element.
 */
function getOrCreateCanvas(containerId, canvasId) {
  const container = document.getElementById(containerId);
  if (!container) {
    throw new Error(`Container #${containerId} not found`);
  }

  let canvas = container.querySelector('canvas#' + canvasId);
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.id = canvasId;
    container.appendChild(canvas);
  }
  return canvas;
}

/**
 * Internal helper: destroy any previous chart on the canvas, create a new
 * Chart instance, store it in the map, and return it.
 */
function _create(canvasId, config) {
  destroyChart(canvasId);
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    throw new Error(`Canvas #${canvasId} not found`);
  }
  const instance = new Chart(canvas, config);
  chartInstances.set(canvasId, instance);
  return instance;
}

// -- Chart factories ------------------------------------------------------

/**
 * 5-axis radar chart for multi-view scores.
 *
 * @param {string} containerId  - wrapper div id
 * @param {string[]} labels     - 5 axis labels
 * @param {Array<{label:string, data:number[], borderColor?:string, backgroundColor?:string}>} datasets
 * @returns {Chart}
 */
function createRadarChart(containerId, labels, datasets) {
  const canvasId = containerId + '-canvas';
  const canvas = getOrCreateCanvas(containerId, canvasId);

  const resolved = datasets.map((ds) => ({
    label: ds.label,
    data: ds.data,
    borderColor: ds.borderColor || '#00d46a',
    backgroundColor: ds.backgroundColor || '#00d46a22',
    pointBackgroundColor: ds.borderColor || '#00d46a',
    pointRadius: 4,
    tension: 0,
    borderWidth: 2,
    fill: true,
  }));

  return _create(canvasId, {
    type: 'radar',
    data: { labels, datasets: resolved },
    options: {
      scales: {
        r: {
          min: 0,
          max: 1,
          ticks: {
            stepSize: 0.2,
            backdropColor: 'transparent',
            color: '#555',
            font: { size: 10 },
          },
          grid: { color: '#2a2a2a' },
          angleLines: { color: '#2a2a2a' },
          pointLabels: {
            color: '#999',
            font: { size: 12, family: 'Outfit' },
          },
        },
      },
      plugins: {
        legend: {
          display: datasets.length > 1,
          position: 'top',
        },
      },
    },
  });
}

/**
 * Doughnut chart for category distribution.
 *
 * @param {string}   containerId
 * @param {string[]} labels
 * @param {number[]} data
 * @param {string[]} [colors]
 * @returns {Chart}
 */
function createDoughnutChart(containerId, labels, data, colors) {
  const canvasId = containerId + '-canvas';
  getOrCreateCanvas(containerId, canvasId);

  const palette = colors || ['#00d46a', '#60a5fa', '#f59e0b'];
  // Extend palette cyclically if more slices than colours
  const bgColors = data.map((_, i) => palette[i % palette.length]);
  const borderColors = bgColors;

  return _create(canvasId, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: bgColors,
          borderColor: borderColors,
          borderWidth: 1,
        },
      ],
    },
    options: {
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
        },
      },
    },
  });
}

/**
 * Horizontal bar chart — feature importance, subcategory counts, etc.
 *
 * @param {string}   containerId
 * @param {string[]} labels
 * @param {number[]} data
 * @param {object}   [options]
 * @param {string}   [options.barColor='#00d46a']
 * @param {boolean}  [options.showValues=false]
 * @returns {Chart}
 */
function createHorizontalBarChart(containerId, labels, data, options) {
  const canvasId = containerId + '-canvas';
  getOrCreateCanvas(containerId, canvasId);

  const barColor = (options && options.barColor) || '#00d46a';
  const showValues = (options && options.showValues) || false;

  const plugins = [];
  if (showValues) {
    plugins.push({
      id: 'barValueLabels',
      afterDatasetsDraw(chart) {
        const { ctx } = chart;
        chart.data.datasets.forEach((dataset, di) => {
          const meta = chart.getDatasetMeta(di);
          meta.data.forEach((bar, index) => {
            const value = dataset.data[index];
            ctx.save();
            ctx.fillStyle = '#999';
            ctx.font = '12px Outfit';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(value, bar.x + 6, bar.y);
            ctx.restore();
          });
        });
      },
    });
  }

  return _create(canvasId, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: barColor,
          borderColor: barColor,
          borderWidth: 0,
          barThickness: 20,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      scales: {
        x: {
          grid: { color: '#2a2a2a' },
          ticks: { color: '#999' },
        },
        y: {
          grid: { display: false },
          ticks: { color: '#999' },
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
    plugins,
  });
}

/**
 * Grouped (side-by-side) bar chart — fusion method comparison.
 *
 * @param {string}   containerId
 * @param {string[]} labels
 * @param {Array<{label:string, data:number[]}>} datasets
 * @returns {Chart}
 */
function createGroupedBarChart(containerId, labels, datasets) {
  const canvasId = containerId + '-canvas';
  getOrCreateCanvas(containerId, canvasId);

  const palette = ['#00d46a', '#60a5fa', '#f59e0b', '#ef4444'];

  const resolved = datasets.map((ds, i) => ({
    label: ds.label,
    data: ds.data,
    backgroundColor: palette[i % palette.length],
    borderColor: palette[i % palette.length],
    borderWidth: 0,
  }));

  return _create(canvasId, {
    type: 'bar',
    data: { labels, datasets: resolved },
    options: {
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#999' },
        },
        y: {
          grid: { color: '#2a2a2a' },
          ticks: { color: '#999' },
        },
      },
      plugins: {
        legend: { position: 'top' },
      },
    },
  });
}

/**
 * Stacked bar chart — pipeline timing, cost breakdown.
 *
 * @param {string}   containerId
 * @param {string[]} labels
 * @param {Array<{label:string, data:number[]}>} datasets
 * @param {object}   [options]
 * @param {'x'|'y'}  [options.indexAxis='x']  - 'y' for horizontal stacked bars
 * @returns {Chart}
 */
function createStackedBarChart(containerId, labels, datasets, options) {
  const canvasId = containerId + '-canvas';
  getOrCreateCanvas(containerId, canvasId);

  const indexAxis = (options && options.indexAxis) || 'x';
  const palette = ['#00d46a', '#00b359', '#008f47'];

  const resolved = datasets.map((ds, i) => ({
    label: ds.label,
    data: ds.data,
    backgroundColor: palette[i % palette.length],
    borderColor: palette[i % palette.length],
    borderWidth: 0,
  }));

  return _create(canvasId, {
    type: 'bar',
    data: { labels, datasets: resolved },
    options: {
      indexAxis,
      scales: {
        x: {
          stacked: true,
          grid: { color: indexAxis === 'y' ? '#2a2a2a' : 'transparent' },
          ticks: { color: '#999' },
        },
        y: {
          stacked: true,
          grid: { color: indexAxis === 'x' ? '#2a2a2a' : 'transparent' },
          ticks: { color: '#999' },
        },
      },
      plugins: {
        legend: { position: 'top' },
      },
    },
  });
}

/**
 * Cost comparison chart — 3 strategies with colour-coded bars and $ labels.
 *
 * @param {string}   containerId
 * @param {string[]} strategies  - e.g. ['cost_optimized','balanced','quality_first']
 * @param {number[]} costs       - e.g. [0.0003, 0.0036, 0.0475]
 * @returns {Chart}
 */
function createCostComparisonChart(containerId, strategies, costs) {
  const canvasId = containerId + '-canvas';
  getOrCreateCanvas(containerId, canvasId);

  // Colour-code: cheapest green, middle amber, most expensive red
  const sorted = [...costs].sort((a, b) => a - b);
  const colorMap = {
    [sorted[0]]: '#00d46a',
    [sorted[1]]: '#f59e0b',
    [sorted[2]]: '#ef4444',
  };
  const bgColors = costs.map((c) => colorMap[c] || '#60a5fa');

  const dollarPlugin = {
    id: 'costValueLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.data.datasets.forEach((dataset, di) => {
        const meta = chart.getDatasetMeta(di);
        meta.data.forEach((bar, index) => {
          const value = dataset.data[index];
          const label = '$' + value.toFixed(4);
          ctx.save();
          ctx.fillStyle = '#e8e8e8';
          ctx.font = '12px Outfit';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillText(label, bar.x, bar.y - 6);
          ctx.restore();
        });
      });
    },
  };

  return _create(canvasId, {
    type: 'bar',
    data: {
      labels: strategies,
      datasets: [
        {
          data: costs,
          backgroundColor: bgColors,
          borderColor: bgColors,
          borderWidth: 0,
        },
      ],
    },
    options: {
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: '#999',
            font: { family: 'Fira Code', size: 11 },
          },
        },
        y: {
          grid: { color: '#2a2a2a' },
          ticks: {
            color: '#999',
            callback: (value) => '$' + value.toFixed(4),
          },
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
    plugins: [dollarPlugin],
  });
}

// -- Exports --------------------------------------------------------------

export {
  destroyChart,
  destroyAllCharts,
  getOrCreateCanvas,
  createRadarChart,
  createDoughnutChart,
  createHorizontalBarChart,
  createGroupedBarChart,
  createStackedBarChart,
  createCostComparisonChart,
};
