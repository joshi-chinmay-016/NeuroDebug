import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/debug': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/workspace': 'http://127.0.0.1:8000',
      '/history': 'http://127.0.0.1:8000',
      '/analytics': 'http://127.0.0.1:8000',
      '/profile': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
