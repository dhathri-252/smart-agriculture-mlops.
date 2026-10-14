import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Allow the local dev hostname http://smart-agriculture:5173
    // (requires a hosts-file entry: 127.0.0.1 smart-agriculture).
    // localhost / 127.0.0.1 keep working as before.
    allowedHosts: ['smart-agriculture', 'localhost', '127.0.0.1'],
  },
  preview: {
    port: 5173,
  },
})
