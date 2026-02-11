import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  root: resolve(__dirname, 'src/renderer'),
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, 'dist/renderer'),
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    open: false,
  },
})
