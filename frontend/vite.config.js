import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // during `npm run dev`, proxy API calls to the FastAPI backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // build straight into the backend's static/ folder so `main.py` can serve it
    outDir: '../backend/static',
    emptyOutDir: true,
  },
})
