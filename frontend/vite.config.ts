import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    proxy: {
      // Financial report data → Node backend (port 9001)
      '/api/data': {
        target: 'http://127.0.0.1:9001',
        changeOrigin: true,
      },
      // All other API routes → Python backend (port 9000)
      '/api': {
        target: 'http://127.0.0.1:9000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
