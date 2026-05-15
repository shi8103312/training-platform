import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Load ports configuration from project root
function loadPortsConfig() {
  try {
    const portsFile = resolve(__dirname, '..', 'ports.json')
    const content = readFileSync(portsFile, 'utf-8')
    return JSON.parse(content)
  } catch (e) {
    return { backend: 8003, frontend: 5173 }
  }
}

const ports = loadPortsConfig()

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: ports.frontend || 5173,
    proxy: {
      '/api': {
        target: `http://localhost:${ports.backend}`,
        changeOrigin: true,
      },
      '/uploads': {
        target: `http://localhost:${ports.backend}`,
        changeOrigin: true,
      },
    },
  },
})
