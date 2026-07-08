<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.chart(currentCode.value))
onMounted(load)
watch(currentCode, load)

const indicators = computed(() => data.value?.indicators || [])
const score = computed(() => data.value?.score ?? null)

// 신호 → 칩 클래스 / 한글
const sigClass = (s) => (s === 'buy' ? 'sig-buy' : s === 'sell' ? 'sig-sell' : 'sig-hold')
const sigKo = (s) => (s === 'buy' ? '매수' : s === 'sell' ? '매도' : '중립')

// 종합 점수 판정
const verdict = computed(() => {
  const v = score.value
  if (v == null) return { label: '-', cls: 'tx-mut' }
  if (v >= 60) return { label: '매수 우위', cls: 'tx-buy' }
  if (v >= 40) return { label: '중립', cls: 'tx-hold' }
  return { label: '매도 우위', cls: 'tx-sell' }
})

// 신호 집계
const tally = computed(() => {
  const t = { buy: 0, hold: 0, sell: 0 }
  indicators.value.forEach((i) => { t[i.signal] = (t[i.signal] || 0) + 1 })
  return t
})
</script>

<template>
  <div v-if="error" class="card"><div class="error">차트 분석 로드 실패: {{ error }}</div></div>
  <div v-else-if="loading || !data" class="card"><div class="loading">분석 중...</div></div>
  <div v-else class="split tech">
    <!-- 기술적 지표 테이블 -->
    <div class="card" style="padding: 0; overflow: hidden;">
      <div style="padding: 14px 16px; border-bottom: 1px solid var(--bd);">
        <span class="card-title">기술적 지표</span>
        <span class="tx-mut" style="font-size: 12px; margin-left: 8px;">기준일 {{ data.as_of || '-' }}</span>
      </div>
      <div style="padding: 0 16px;">
        <div class="ind-table">
          <div class="ind-row head">
            <span>지표</span><span>값 · 상태</span><span class="ind-sig">신호</span>
          </div>
          <div v-for="i in indicators" :key="i.name" class="ind-row">
            <span class="ind-nm">{{ i.name }}</span>
            <span class="ind-val">{{ i.value }} · {{ i.state }}</span>
            <span class="ind-sig"><span class="sig-chip" :class="sigClass(i.signal)">{{ sigKo(i.signal) }}</span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 종합 기술 점수 -->
    <div class="card signal-card">
      <div class="mini-label">종합 기술 점수</div>
      <div class="big-score" :class="verdict.cls">{{ score == null ? '-' : score }}</div>
      <div :class="verdict.cls" style="font-size: 13px; font-weight: 600;">{{ verdict.label }}</div>
      <div class="divider"></div>
      <div class="tally">
        <div class="tally-row"><span>매수 신호</span><span class="n tx-buy">{{ tally.buy }}</span></div>
        <div class="tally-row"><span>중립 신호</span><span class="n tx-hold">{{ tally.hold }}</span></div>
        <div class="tally-row"><span>매도 신호</span><span class="n tx-sell">{{ tally.sell }}</span></div>
      </div>
      <div class="divider"></div>
      <div class="tx-mut" style="font-size: 11px; line-height: 1.6; text-align: left;">
        RSI·MACD·이동평균·볼린저·스토캐스틱·거래량(OBV) 6개 지표의 매수/매도 신호를 집계한 점수입니다.
      </div>
    </div>
  </div>
</template>
