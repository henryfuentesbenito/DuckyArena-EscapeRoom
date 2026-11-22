import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // <-- Añade esta línea

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
  base: env.VITE_BASE_PATH || '/static/training_build/',
  build: { outDir: '../apps/portal/static/training_build', emptyOutDir: true },
  plugins: [
    react(),
    tailwindcss(), // <-- Añade esta línea
  ],
  }
})
