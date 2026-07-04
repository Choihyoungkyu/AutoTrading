<script setup>
import { computed, onMounted } from 'vue'
import { useKrxStock } from '../composables/useStock.js'
import { currentCode, currentName } from '../composables/useCurrentStock.js'

const { data, error, loading, ensureLoaded } = useKrxStock()
onMounted(ensureLoaded)

const latest = computed(() => {
  const d = data.value?.data
  return d && d.length ? d[d.length - 1] : null
})
const change = computed(() => (latest.value ? parseFloat(latest.value.change) : 0))
const changeClass = computed(() => (change.value > 0 ? 'value-up' : 'value-down'))
const changeText = computed(
  () => (change.value > 0 ? '+' : '') + change.value.toFixed(2) + '%'
)
const fmt = (n) => n.toLocaleString()
const volM = (v) => (v / 1000000).toFixed(1) + 'M'
</script>

<template>
  <div class="card">
    <h2>🇰🇷 국내 주식 데이터 (PYKRX)</h2>
    <p>{{ currentName }} ({{ currentCode }})</p>
    <div v-if="error" class="error">오류: {{ error }}</div>
    <div v-else-if="loading || !latest" class="loading">데이터 로드 중...</div>
    <div v-else style="display: grid; gap: 12px; margin-top: 15px;">
      <div><strong>종목명:</strong> {{ currentName }}</div>
      <div><strong>코드:</strong> {{ currentCode }}</div>
      <div>
        <strong>현재가:</strong>
        <span style="font-size: 24px; font-weight: bold;">{{ fmt(latest.close) }}</span> ₩
      </div>
      <div>
        <strong>변화율:</strong>
        <span :class="changeClass" style="font-size: 18px;">{{ changeText }}</span>
      </div>
      <div><strong>거래량:</strong> {{ volM(latest.volume) }}</div>
      <div><strong>기준일:</strong> {{ latest.date }}</div>
      <div><strong>조회:</strong> {{ data.count }}개 날짜 데이터</div>
    </div>
  </div>
</template>
