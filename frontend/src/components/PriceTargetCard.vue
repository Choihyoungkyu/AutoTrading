<script setup>
import { onMounted, ref } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'

const expectedReturn = ref(0.15)
const maxLoss = ref(0.10)

const { data, error, loading, load } = useAsyncData(
  () => api.priceTarget(expectedReturn.value, maxLoss.value)
)
onMounted(load)

function pct(v) { return Math.round(v * 100) }
function won(v) { return v != null ? v.toLocaleString() + '원' : '-' }
</script>

<template>
  <div class="card">
    <h2>🎯 목표가 · 손절 라인 (이슈 006)</h2>
    <div v-if="error" class="error">목표가 로드 실패: {{ error }}</div>
    <div v-else-if="loading || !data" class="loading">계산 중...</div>
    <div v-else style="margin-top: 15px;">
      <div style="font-size: 13px; color: #7f8c8d; margin-bottom: 12px;">
        현재가 <strong style="color:#2c3e50; font-size:16px;">{{ won(data.current_price) }}</strong>
        · 기준일 {{ data.as_of }}
      </div>

      <div class="pt-grid">
        <div class="metric-box pt-target">
          <div class="metric-label">목표가 (+{{ pct(data.expected_return) }}%)</div>
          <div class="metric-value value-up">{{ won(data.target_price) }}</div>
        </div>
        <div class="metric-box pt-stop">
          <div class="metric-label">손절가 (−{{ pct(data.max_loss) }}%)</div>
          <div class="metric-value value-down">{{ won(data.stop_loss) }}</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">리스크/리워드 비율</div>
          <div class="metric-value">{{ data.risk_reward_ratio ?? '-' }}</div>
        </div>
      </div>

      <div class="pt-controls">
        <label>
          기대수익률: <strong>{{ pct(expectedReturn) }}%</strong>
          <input type="range" min="0.05" max="0.5" step="0.05"
                 v-model.number="expectedReturn" @change="load" />
        </label>
        <label>
          최대손실률: <strong>{{ pct(maxLoss) }}%</strong>
          <input type="range" min="0.05" max="0.3" step="0.05"
                 v-model.number="maxLoss" @change="load" />
        </label>
      </div>

      <div style="font-size: 11px; color: #adb5bd; margin-top: 12px;">
        목표가 = 현재가 ×(1+기대수익률) · 손절가 = 현재가 ×(1−최대손실률)
        · RR = 상승폭 ÷ 하락폭
      </div>
    </div>
  </div>
</template>
