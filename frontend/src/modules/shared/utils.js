/**
 * frontend/src/modules/shared/utils.js
 * =======================================
 * Global UI utilities: toast notifications, loading overlay.
 */

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'info'} type
 * @param {number} duration — ms to display
 */
export function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  toast.innerHTML = `<span aria-hidden="true">${icons[type] ?? 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toast-in 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Show the full-page loading overlay.
 * @param {string} text
 */
export function showLoading(text = 'Computing…') {
  const overlay = document.getElementById('loading-overlay');
  if (!overlay) return;
  document.getElementById('loading-text').textContent = text;
  overlay.hidden = false;
  overlay.setAttribute('aria-hidden', 'false');
}

/**
 * Hide the loading overlay.
 */
export function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (!overlay) return;
  overlay.hidden = true;
  overlay.setAttribute('aria-hidden', 'true');
}

/**
 * Format a number with thousands separators and appropriate decimal places.
 * @param {number} n
 * @param {number} maxDecimals
 * @returns {string}
 */
export function formatNumber(n, maxDecimals = 4) {
  if (n === undefined || n === null || isNaN(n)) return '—';
  if (Math.abs(n) >= 1e6)  return n.toExponential(3);
  if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', { maximumFractionDigits: 0 });
  return n.toFixed(maxDecimals);
}

/**
 * Debounce a function call.
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
export function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
