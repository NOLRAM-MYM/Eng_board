/**
 * frontend/src/modules/shared/api.js
 * =====================================
 * Centralised Axios-based API client.
 *
 * All scientific module API calls go through this client to ensure:
 *   - Consistent CSRF header injection
 *   - Unified error handling
 *   - Base URL management
 */

import axios from 'axios';

// Read CSRF token from the meta tag set by Django's base template
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ?? '';

/**
 * Axios instance for all API calls.
 * Vite proxies /api/* to http://localhost:8000 (see vite.config.js).
 */
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken,
  },
  timeout: 30_000,  // 30 seconds — complex calculations can take time
});

// Response interceptor — unwrap our {"status": "success", "data": ...} envelope
apiClient.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (body?.status === 'success') {
      return body.data;
    }
    return body;
  },
  (error) => {
    const errorData = error.response?.data;
    console.error('[API Error]', errorData ?? error.message);
    return Promise.reject(errorData ?? error);
  },
);

// ----------------------------------------------------------------
// Module-specific API functions
// ----------------------------------------------------------------

/** Fluids — Pipe Flow */
export const fluidsAPI = {
  /** Compute pipe flow analysis. @param {Object} params */
  async calculate(params) {
    return apiClient.post('/fluids/pipe-flow/calculate/', params);
  },
  /** Get input schema + fluid presets. */
  async getSchema() {
    return apiClient.get('/fluids/pipe-flow/schema/');
  },
};

/** Materials — Beam Deflection */
export const materialsAPI = {
  async beamDeflection(params) {
    return apiClient.post('/materials/beam-deflection/', params);
  },
};

/** Chemistry — Element Properties */
export const chemistryAPI = {
  async getElement(identifier) {
    return apiClient.get(`/chemistry/element/${identifier}/`);
  },
};

export default apiClient;
