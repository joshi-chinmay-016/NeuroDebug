import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/debug': 'http://15.206.92.74:8000',
      '/health': 'http://15.206.92.74:8000',
    },
  },
})
