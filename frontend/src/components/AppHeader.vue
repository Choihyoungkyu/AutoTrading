<script setup>
import { computed, onMounted } from 'vue'
import { useHealth } from '../composables/useStock.js'
import { currentCode, currentName, goHome } from '../composables/useCurrentStock.js'
import { isFavorite, toggleFavorite } from '../composables/useWatchlist.js'
import StockSearch from './StockSearch.vue'

const faved = computed(() => isFavorite(currentCode.value))

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
    <div class="header-top">
      <button class="home-btn" @click="goHome">← 홈</button>
      <h1>📈 주식 분석 시스템 v1.0</h1>
    </div>

    <StockSearch />

    <div class="status">
      <div class="status-item">
        <span class="status-badge">현재 종목</span>
        <span><strong>{{ currentName }}</strong> ({{ currentCode }})</span>
        <button
          class="fav-btn"
          :class="{ on: faved }"
          :title="faved ? '관심 종목 해제' : '관심 종목 추가'"
          @click="toggleFavorite(currentCode, currentName)"
        >{{ faved ? '❤️' : '🤍' }}</button>
      </div>
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
