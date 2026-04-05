import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core libraries (rarely changes, good for long-term caching)
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],

          // UI component libraries (stable, large)
          'ui-vendor': [
            '@radix-ui/react-alert-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-label',
            '@radix-ui/react-progress',
            '@radix-ui/react-select',
            '@radix-ui/react-slot',
            '@radix-ui/react-switch',
            '@radix-ui/react-tabs',
            '@radix-ui/react-tooltip',
          ],

          // Analytics & Charts (large, only for specific pages)
          'charts-vendor': ['recharts'],

          // React Query & data fetching
          'query-vendor': ['@tanstack/react-query', 'axios'],

          // Form handling
          'form-vendor': ['react-hook-form', '@hookform/resolvers', 'zod'],

          // Utilities
          'utils-vendor': ['date-fns', 'clsx', 'tailwind-merge', 'class-variance-authority'],

          // Resium (cesium is externalized by vite-plugin-cesium)
          'cesium-vendor': ['cesium', 'resium'],

          // deck.gl (high-performance data overlays)
          'deckgl-vendor': ['@deck.gl/core', '@deck.gl/layers', '@deck.gl/geo-layers'],
        },
      },
    },
    // Warn if chunks exceed 500 KB (already achieved with code splitting)
    chunkSizeWarningLimit: 500,
  },
  server: {
    host: true, // Listen on all network interfaces
    port: 3000,
    proxy: {
      '/api/v1': {
        // fmp-service runs in host network mode, accessible via host IP
        target: 'http://localhost:8113',
        changeOrigin: true,
      },
      // NOTE: /api/execution proxy removed - execution-service archived (2025-12-28)
      '/api/prediction': {
        // prediction-service proxy (uses host IP like fmp-service)
        target: 'http://localhost:8116',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/prediction/, '/api'),
      },
      // Separate route for SSE streaming endpoint (no buffering)
      '/api/prediction/v1/strategy-lab/backtest/stream': {
        target: 'http://localhost:8116',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/prediction/, '/api'),
        // Disable buffering for SSE
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            // Set headers to prevent buffering
            proxyReq.setHeader('X-Accel-Buffering', 'no');
          });
        },
      },
      '/api/geospatial': {
        target: 'http://localhost:8124',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/geospatial/, '/api'),
      },
      '/ws/spatial': {
        target: 'ws://localhost:8124',
        ws: true,
        changeOrigin: true,
      },
      '/ws/graph': {
        target: 'ws://localhost:8124',
        ws: true,
        changeOrigin: true,
      },
      '/ws': {
        // fmp-service runs in host network mode, accessible via host IP
        target: 'ws://localhost:8113',
        ws: true, // Enable WebSocket proxying
        changeOrigin: true,
      },

    },
  },
  define: {
    CESIUM_BASE_URL: JSON.stringify('/'),
  },
  optimizeDeps: {
    include: ['react-is', 'cesium'],
  },
})
