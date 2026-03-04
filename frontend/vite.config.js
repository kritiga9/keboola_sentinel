import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Output to ../static so FastAPI (running from /app) serves from /app/static
    outDir: '../static',
    emptyOutDir: true,
    sourcemap: false,
  },
})
