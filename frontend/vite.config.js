import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, /api se redirige al API Gateway (nginx) que corre en :8080.
// En producción, el nginx que sirve el frontend hace el mismo proxy (ver Dockerfile/nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    // Escucha en todas las interfaces para permitir acceso desde la LAN en desarrollo.
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8080',
        changeOrigin: true,
      },
      // Imágenes servidas por property-service (a través del gateway)
      '/static': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/static/, '/api/properties/static'),
      },
    },
  },
  // Vista previa del build de producción (npm run preview) también en la LAN.
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
})
