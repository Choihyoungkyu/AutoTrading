<script setup>
import { computed, onMounted } from 'vue'
import { useHealth } from '../composables/useStock.js'

const { data, error, ensureLoaded } = useHealth()
onMounted(ensureLoaded)

const dbText = computed(() => {
  if (error.value) return '✗ 오류'
  if (!data.value) return '연결 중...'
  return data.value.status === 'ok' ? '✓ 정상 연결' : '✗ 연결 실패'
})
const dbColor = computed(() => {
  if (!data.value || error.value) return error.value ? '#e74c3c' : ''
  return data.value.status === 'ok' ? '#27ae60' : '#e74c3c'
})
</script>

<template>
  <header>
    <h1>📈 주식 분석 시스템 v1.0</h1>
    <p>PYKRX와 yfinance를 기반으로 한 다중 종목 분석 플랫폼</p>
    <div class="status">
      <div class="status-item">
        <span class="status-badge">데이터베이스</span>
        <span :style="{ color: dbColor }">{{ dbText }}</span>
      </div>
      <div class="status-item">
        <span class="status-badge">API Server</span>
        <span>http://localhost:8000</span>
      </div>
    </div>
  </header>
</template>
