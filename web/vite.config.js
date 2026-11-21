import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend for the dev/preview proxy. Override with API_URL=http://localhost:8001 npm run dev
const target = process.env.API_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target, changeOrigin: true } },
  },
  preview: {
    port: 4173,
    proxy: { '/api': { target, changeOrigin: true } },
  },
})
