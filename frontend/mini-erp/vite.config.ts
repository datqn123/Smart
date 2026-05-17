/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // AI chat SSE: rule riêng trước /api — http-proxy hay buffer POST stream.
      "/api/v1/ai/chat/stream": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
        timeout: 600_000,
        proxyTimeout: 600_000,
        configure: (proxy) => {
          proxy.on("proxyRes", (proxyRes) => {
            proxyRes.headers["cache-control"] = "no-cache, no-transform"
            proxyRes.headers["x-accel-buffering"] = "no"
          })
        },
      },
      // Cùng origin: fetch('/api/...') → Spring trên 8080 (envelope JSON), không trúng index.html của Vite.
      "/api": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
        timeout: 600_000,
        proxyTimeout: 600_000,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
