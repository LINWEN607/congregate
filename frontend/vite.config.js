import { defineConfig } from 'vite'
import createVuePlugin from '@vitejs/plugin-vue'

const path = require("path");

export default defineConfig({
  plugins: [
    createVuePlugin(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  }
})