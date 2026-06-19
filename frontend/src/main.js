/**
 * frontend/src/main.js
 * ======================
 * Vite entry point — imports shared styles and global utilities.
 * Page-specific logic lives in frontend/src/pages/*.js
 */

// Global styles
import './styles/dashboard.css';

// Global utilities available on window (for Django template usage)
import { showToast, showLoading, hideLoading } from './modules/shared/utils.js';

window.showToast   = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;

console.log('[SciDash] Frontend bundle loaded.');
