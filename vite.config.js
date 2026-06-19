// =============================================================================
// vite.config.js — Vite Build Configuration for Scientific Dashboard
// =============================================================================
import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';
import path from 'path';

export default defineConfig({
  // Root of frontend source files
  root: path.resolve(__dirname, 'frontend/src'),

  // Where Vite serves static assets from during dev
  publicDir: path.resolve(__dirname, 'frontend/public'),

  plugins: [
    // Generates legacy bundles for older browsers (IE11+, pre-ES2015 targets)
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),
  ],

  resolve: {
    alias: {
      // Convenient import alias: '@/modules/...' → 'frontend/src/modules/...'
      '@': path.resolve(__dirname, 'frontend/src'),
    },
  },

  build: {
    // Output goes into Django's staticfiles directory so `collectstatic` picks it up
    outDir: path.resolve(__dirname, 'frontend/dist'),
    emptyOutDir: true,

    // Generate a manifest.json so Django can reference hashed filenames
    manifest: true,

    rollupOptions: {
      input: {
        // One entry point per dashboard page
        main:    path.resolve(__dirname, 'frontend/src/main.js'),
        fluids:  path.resolve(__dirname, 'frontend/src/pages/fluids.js'),
        materials: path.resolve(__dirname, 'frontend/src/pages/materials.js'),
        chemistry: path.resolve(__dirname, 'frontend/src/pages/chemistry.js'),
      },
      output: {
        // Clean, readable chunk names
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },

    // Enable minification in production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false, // Keep console.log during development
      },
    },

    // Source maps for debugging
    sourcemap: process.env.NODE_ENV !== 'production',
  },

  server: {
    // Vite dev server port — Django runs on 8000, Vite on 5173
    port: 5173,
    strictPort: true,

    // Proxy API calls to Django backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  css: {
    // Enable PostCSS (autoprefixer configured in postcss.config.js)
    postcss: path.resolve(__dirname, 'postcss.config.js'),
  },
});
