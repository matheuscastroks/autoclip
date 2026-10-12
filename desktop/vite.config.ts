import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({ plugins:[vue()], test:{environment:'jsdom',globals:true,maxWorkers:2},server:{host:'127.0.0.1'} })
