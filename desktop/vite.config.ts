import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver({ importStyle: false })],
    }),
  ],
  test: {
    environment: 'jsdom',
    globals: true,
    maxWorkers: 2,
    testTimeout: 15000,
    setupFiles: ['./tests/setup.ts'],
  },
  server: { host: '127.0.0.1' },
})
