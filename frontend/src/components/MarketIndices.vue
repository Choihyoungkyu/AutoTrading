<script setup>
import { onMounted } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'

// 홈 화면 상단: 주요 지수(코스피·코스닥·나스닥·S&P500·다우) 가격·등락률
const { data, error, loading, load } = useAsyncData(() => api.indices())
onMounted(load)

function fmtPrice(v) {
  return Number(v).toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtChange(v) {
  const n = Number(v)
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toLocaleString('ko-KR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
function dir(rate) {
  if (rate > 0) return 'up'
  if (rate < 0) return 'down'
  return 'flat'
}
function arrow(rate) {
  if (rate > 0) return '▲'
  if (rate < 0) return '▼'
  return '−'
}
</script>

<template>
  <section class="indices">
    <div v-if="loading" class="indices-msg">지수 불러오는 중...</div>
    <div v-else-if="error" class="indices-msg error">지수를 불러오지 못했습니다.</div>
    <div v-else class="indices-grid">
      <div
        v-for="idx in data"
        :key="idx.name"
        class="index-card"
        :class="dir(idx.changeRate)"
      >
        <div class="index-name">{{ idx.name }}</div>
        <template v-if="idx.error">
          <div class="index-price muted">—</div>
        </template>
        <template v-else>
          <div class="index-price">{{ fmtPrice(idx.price) }}</div>
          <div class="index-change">
            {{ arrow(idx.changeRate) }} {{ fmtChange(idx.change) }}
            ({{ fmtChange(idx.changeRate) }}%)
          </div>
        </template>
      </div>
    </div>
  </section>
</template>
