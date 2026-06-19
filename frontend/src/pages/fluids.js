/**
 * frontend/src/pages/fluids.js
 * ==============================
 * Vite page bundle entry point for the Fluid Mechanics dashboard.
 *
 * This file is referenced as a Rollup input in vite.config.js.
 * It imports all fluids-specific modules and wires them together.
 *
 * In production, Django loads the hashed bundle from frontend/dist/.
 * In development, Vite's dev server serves this directly.
 */

import './styles/dashboard.css';
import { fluidsAPI } from './modules/shared/api.js';
import { showToast, showLoading, hideLoading, formatNumber } from './modules/shared/utils.js';
import { PlotlyCharts } from './modules/fluids/fluids-plotly.js';
import { ThreePipe } from './modules/fluids/fluids-three.js';

// Make available to Django template inline JS (fallback path)
window.showToast   = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;

// -----------------------------------------------------------------
// Form Manager
// -----------------------------------------------------------------
async function initFluidsPage() {
  // Load schema + presets
  try {
    const schema = await fluidsAPI.getSchema();
    populatePresets(schema.preset_fluids || []);
  } catch (e) {
    console.warn('[Fluids] Schema load failed:', e);
  }

  // Init Three.js scene
  ThreePipe.init('three-canvas');

  // Form submit
  const form = document.getElementById('pipe-flow-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await handleCalculate();
    });
  }

  // Preset selector
  const presetSelect = document.getElementById('fluid-preset');
  if (presetSelect) {
    presetSelect.addEventListener('change', onPresetChange);
  }
}

function populatePresets(presets) {
  const select = document.getElementById('fluid-preset');
  if (!select) return;
  select.dataset.presets = JSON.stringify(presets);
  presets.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.name;
    opt.textContent = p.name;
    select.appendChild(opt);
  });
}

function onPresetChange(e) {
  const select  = e.target;
  const presets = JSON.parse(select.dataset.presets || '[]');
  const preset  = presets.find(p => p.name === e.target.value);
  if (preset) {
    document.getElementById('density_kg_m3').value   = preset.density;
    document.getElementById('viscosity_mpa_s').value  = preset.viscosity;
    showToast(`Preset loaded: ${preset.name}`, 'info', 2500);
  }
}

function getFormData() {
  const v = (id) => parseFloat(document.getElementById(id)?.value);
  const i = (id) => parseInt(document.getElementById(id)?.value) || 0;
  return {
    diameter_mm:          v('diameter_mm'),
    length_m:             v('length_m'),
    roughness_mm:         v('roughness_mm'),
    density_kg_m3:        v('density_kg_m3'),
    viscosity_mpa_s:      v('viscosity_mpa_s'),
    flow_rate_lpm:        v('flow_rate_lpm'),
    num_elbows_90:        i('num_elbows_90'),
    num_gate_valves_open: i('num_gate_valves_open'),
    num_check_valves:     i('num_check_valves'),
  };
}

async function handleCalculate() {
  const data = getFormData();

  // Client-side guard checks
  if (!data.diameter_mm || data.diameter_mm <= 0) {
    showToast('Diameter must be positive.', 'error');
    return;
  }
  if (data.flow_rate_lpm < 0) {
    showToast('Flow rate must be non-negative.', 'error');
    return;
  }

  const btn = document.getElementById('calculate-btn');
  if (btn) { btn.disabled = true; btn.querySelector('#btn-text').textContent = 'Computing…'; }
  showLoading('Running Darcy-Weisbach analysis…');

  try {
    const result = await fluidsAPI.calculate(data);
    updateUI(result);
    PlotlyCharts.renderPressureDrop(result, data.flow_rate_lpm);
    PlotlyCharts.renderVelocityProfile(result);
    ThreePipe.updateParticles(result);
    showToast('Calculation complete!', 'success');
  } catch (err) {
    const msg = err?.errors
      ? Object.entries(err.errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`).join(' | ')
      : (err?.message || 'Server error. Check console.');
    showToast(`Error: ${msg}`, 'error', 7000);
    console.error('[Calculate Error]', err);
  } finally {
    if (btn) { btn.disabled = false; btn.querySelector('#btn-text').textContent = 'Calculate'; }
    hideLoading();
  }
}

function updateUI(result) {
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

  set('kpi-velocity-val',  result.velocity_m_s.toFixed(3));
  set('kpi-re-val',        formatNumber(result.reynolds_number, 0));
  set('kpi-friction-val',  result.friction_factor.toFixed(6));
  set('kpi-dp-major-val',  formatNumber(result.pressure_drop_major_pa, 1));
  set('kpi-dp-minor-val',  formatNumber(result.pressure_drop_minor_pa, 1));
  set('kpi-dp-total-val',  result.pressure_drop_total_bar.toFixed(5));

  set('regime-value', result.flow_regime);
  set('re-value',     formatNumber(result.reynolds_number, 0));
  set('dp-value',     result.pressure_drop_total_bar.toFixed(4) + ' bar');

  // Table
  set('tbl-velocity',     result.velocity_m_s.toFixed(4) + ' m/s');
  set('tbl-re',           formatNumber(result.reynolds_number, 0));
  set('tbl-regime',       result.flow_regime);
  set('tbl-ff',           result.friction_factor.toFixed(8));
  set('tbl-ffmethod',     result.friction_method);
  set('tbl-dp-major',     formatNumber(result.pressure_drop_major_pa, 2));
  set('tbl-dp-minor',     formatNumber(result.pressure_drop_minor_pa, 2));
  set('tbl-dp-total-pa',  formatNumber(result.pressure_drop_total_pa, 2));
  set('tbl-dp-total-bar', result.pressure_drop_total_bar.toFixed(6));

  // Hagen-Poiseuille
  const hpCard = document.getElementById('hp-card');
  if (hpCard) {
    if (result.hagen_poiseuille_exact && result.flow_regime === 'Laminar') {
      hpCard.style.display = 'block';
      const hpEl = document.getElementById('hp-formula');
      hpEl.innerHTML = `\\[ \\Delta P = ${result.hagen_poiseuille_exact} \\text{ Pa} \\]`;
      window.MathJax?.typesetPromise([hpEl]);
    } else {
      hpCard.style.display = 'none';
    }
  }

  // Warnings
  const wc = document.getElementById('warnings-container');
  if (wc) {
    wc.style.display = result.warnings?.length ? 'block' : 'none';
    wc.innerHTML = (result.warnings || [])
      .map(w => `<div class="warning-item"><span>⚠</span><span>${w}</span></div>`)
      .join('');
  }
}

// Boot
document.addEventListener('DOMContentLoaded', initFluidsPage);
