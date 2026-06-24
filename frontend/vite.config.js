import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 개발: Vite dev server(5173)가 /api·/analyze 요청을 Flask(8000)로 프록시
// 배포: dist/로 빌드 → Flask가 정적 서빙
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/analyze': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  base: '/',
})
