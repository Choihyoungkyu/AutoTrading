<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.recommendation(currentCode.value))
onMounted(load)
watch(currentCode, load)

const gradeLabel = computed(() => {
  const g = data.value?.grade
  return g === 'buy' ? 'BUY (매수)' : g === 'sell' ? 'SELL (매도)' : 'HOLD (관망)'
})
const gradeClass = computed(() => {
  const g = data.value?.grade
  return 'verdict-' + (g === 'buy' ? 'undervalued' : g === 'sell' ? 'overvalued' : 'neutral')
})

const parts = computed(() => {
  const d = data.value
  if (!d) return []
  return [
    { key: '재무', score: d.components.financial, weight: d.weights.financial },
    { key: '차트', score: d.components.chart, weight: d.weights.chart },
    { key: '뉴스', score: d.components.news, weight: d.weights.news },
  ]
})
function pct(v) { return Math.round(v * 100) }
</script>

<template>
  <div class="card">
    <h2>🎯 종합 추천 (이슈 005)</h2>
    <div v-if="error" class="error">추천 로드 실패: {{ error }}</div>
    <div v-else-if="loading || !data" class="loading">종합 분석 중...</div>
    <div v-else style="margin-top: 15px;">
      <div style="text-align: center; margin-bottom: 20px;">
        <div class="verdict-badge rec-grade" :class="gradeClass">{{ gradeLabel }}</div>
        <div style="font-size: 13px; color: #7f8c8d; margin-top: 10px;">
          종합 점수 <strong style="color:#2c3e50; font-size:16px;">{{ data.score }}</strong> / 1.0
        </div>
        <div style="font-size: 13px; color: #495057; margin-top: 8px;">{{ data.reasoning }}</div>
      </div>

      <div class="rec-parts">
        <div v-for="p in parts" :key="p.key" class="rec-part">
          <div class="rec-part-head">
            <span>{{ p.key }}</span>
            <span style="color:#adb5bd;">가중치 {{ pct(p.weight) }}%</span>
          </div>
          <div class="rec-bar"><div class="rec-bar-fill" :style="{ width: pct(p.score) + '%' }"></div></div>
          <div class="rec-part-score">{{ p.score }}</div>
        </div>
      </div>

      <div style="font-size: 11px; color: #adb5bd; margin-top: 14px;">
        기준: 재무 30% + 차트 40% + 뉴스 30% 가중평균 · Buy &gt; 0.65 / Hold 0.35~0.65 / Sell &lt; 0.35
      </div>
    </div>
  </div>
</template>
