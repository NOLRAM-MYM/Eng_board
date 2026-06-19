/**
 * frontend/src/modules/fluids/fluids-plotly.js
 * ================================================
 * Plotly.js chart renderers for the Fluid Mechanics dashboard.
 *
 * Exports:
 *   PlotlyCharts.renderPressureDrop(result, operatingFlowLPM)
 *   PlotlyCharts.renderVelocityProfile(result)
 */

import Plotly from 'plotly.js-dist';

// Shared dark-mode Plotly layout base
const DARK_LAYOUT_BASE = {
  paper_bgcolor: 'transparent',
  plot_bgcolor:  '#0d1526',
  font: {
    family: 'Inter, system-ui, sans-serif',
    color:  '#94a3b8',
    size:   11,
  },
  margin: { t: 12, r: 16, b: 52, l: 72 },
  xaxis: {
    gridcolor:     'rgba(255,255,255,0.05)',
    zerolinecolor: 'rgba(255,255,255,0.1)',
    tickfont: { family: 'JetBrains Mono, monospace', size: 10 },
  },
  yaxis: {
    gridcolor:     'rgba(255,255,255,0.05)',
    zerolinecolor: 'rgba(255,255,255,0.1)',
    tickfont: { family: 'JetBrains Mono, monospace', size: 10 },
  },
  legend: { bgcolor: 'rgba(0,0,0,0)', borderwidth: 0, font: { size: 10 } },
  hovermode: 'x unified',
};

const PLOTLY_CONFIG = {
  responsive:    true,
  displaylogo:   false,
  modeBarButtonsToRemove: ['toImage', 'sendDataToCloud', 'select2d', 'lasso2d'],
};

export const PlotlyCharts = {
  _pdRendered: false,
  _vpRendered: false,

  /**
   * Render the Pressure Drop vs Flow Rate sweep chart.
   *
   * @param {Object} result         — API response data
   * @param {number} operatingFlowLPM — current operating flow rate [L/min]
   */
  renderPressureDrop(result, operatingFlowLPM) {
    const containerId = 'plotly-chart';
    const el = document.getElementById(containerId);
    if (!el) return;

    // Convert SI units to user-friendly display units
    const qLPM  = result.sweep_flow_rates_m3_s.map(q => q * 60_000);  // m³/s → L/min
    const dpBar = result.sweep_pressure_drops_pa.map(p => p / 1e5);   // Pa → bar

    // Operating point (current calculation)
    const opDpBar = result.pressure_drop_total_bar;

    const traces = [
      // Main curve
      {
        x: qLPM,
        y: dpBar,
        mode: 'lines',
        name: 'ΔP vs Q curve',
        line: { color: '#3b82f6', width: 2.5, shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(59,130,246,0.06)',
        hovertemplate: 'Q: %{x:.1f} L/min<br>ΔP: %{y:.4f} bar<extra></extra>',
      },
      // Operating point marker
      {
        x: [operatingFlowLPM],
        y: [opDpBar],
        mode: 'markers',
        name: 'Operating Point',
        marker: {
          color: '#ef4444',
          size:   11,
          symbol: 'circle',
          line:   { color: '#fff', width: 1.5 },
        },
        hovertemplate: 'Operating Point<br>Q: %{x:.1f} L/min<br>ΔP: %{y:.5f} bar<extra></extra>',
      },
    ];

    const layout = {
      ...DARK_LAYOUT_BASE,
      xaxis: {
        ...DARK_LAYOUT_BASE.xaxis,
        title: { text: 'Volumetric Flow Rate  (L/min)', font: { size: 11, color: '#64748b' } },
      },
      yaxis: {
        ...DARK_LAYOUT_BASE.yaxis,
        title: { text: 'Pressure Drop  (bar)', font: { size: 11, color: '#64748b' } },
      },
      // Vertical line at operating flow rate
      shapes: [
        {
          type: 'line',
          x0: operatingFlowLPM, x1: operatingFlowLPM,
          y0: 0, y1: opDpBar,
          line: { color: 'rgba(239,68,68,0.4)', dash: 'dot', width: 1.5 },
        },
      ],
    };

    // Remove placeholder
    document.getElementById('chart-placeholder')?.remove();

    if (!this._pdRendered) {
      Plotly.newPlot(containerId, traces, layout, PLOTLY_CONFIG);
      this._pdRendered = true;
    } else {
      Plotly.react(containerId, traces, layout, PLOTLY_CONFIG);
    }
  },

  /**
   * Render the Radial Velocity Profile chart.
   *
   * @param {Object} result — API response data
   */
  renderVelocityProfile(result) {
    const containerId = 'profile-chart';
    const el = document.getElementById(containerId);
    if (!el) return;

    const isLaminar = result.flow_regime === 'Laminar';
    const lineColor  = isLaminar ? '#8b5cf6' : '#ef4444';
    const fillColor  = isLaminar ? 'rgba(139,92,246,0.08)' : 'rgba(239,68,68,0.08)';

    const traces = [
      {
        x: result.velocity_profile,
        y: result.radial_positions,
        mode: 'lines',
        name: `v(r) — ${result.flow_regime}`,
        line: { color: lineColor, width: 2.5, shape: 'spline' },
        fill: 'tozerox',
        fillcolor: fillColor,
        hovertemplate: 'v: %{x:.3f} m/s<br>r/R: %{y:.3f}<extra></extra>',
      },
    ];

    const layout = {
      ...DARK_LAYOUT_BASE,
      margin: { t: 10, r: 16, b: 48, l: 62 },
      xaxis: {
        ...DARK_LAYOUT_BASE.xaxis,
        title: { text: 'Velocity  (m/s)', font: { size: 10, color: '#64748b' } },
      },
      yaxis: {
        ...DARK_LAYOUT_BASE.yaxis,
        title: { text: 'r/R  (0=centre, 1=wall)', font: { size: 10, color: '#64748b' } },
        range: [0, 1],
        autorange: false,
      },
      annotations: [
        {
          x: result.velocity_profile[0],
          y: 0.05,
          text: isLaminar ? '📐 Parabolic (Hagen-Poiseuille)' : '〰 Power Law (1/7th)',
          showarrow: false,
          font: { size: 9, color: '#64748b' },
          xanchor: 'left',
        },
      ],
    };

    document.getElementById('profile-placeholder')?.remove();

    if (!this._vpRendered) {
      Plotly.newPlot(containerId, traces, layout, PLOTLY_CONFIG);
      this._vpRendered = true;
    } else {
      Plotly.react(containerId, traces, layout, PLOTLY_CONFIG);
    }
  },
};
