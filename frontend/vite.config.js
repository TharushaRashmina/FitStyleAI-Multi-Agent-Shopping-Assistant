import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Vite configuration for the FitStyle AI frontend.
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
})