import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://api:5045',
        changeOrigin: true
      },
      '/temp': {
        target: 'http://api:5045',
        changeOrigin: true
      },
      '/hubs': {
        target: 'http://api:5045',
        ws: true,
        changeOrigin: true
      }
    }
  }
})
