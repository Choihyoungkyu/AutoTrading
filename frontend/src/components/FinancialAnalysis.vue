<script setup>
import { computed, onMounted } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'

const { data, error, loading, load } = useAsyncData(() => api.financial())
onMounted(load)

const verdictClass = computed(() => {
  const v = data.value?.verdict
  return 'verdict-' + (v === '저평가' ? 'undervalued' : v === '고평가' ? 'overvalued' : 'neutral')
})
const perStatus = computed(() =>
  data.value && data.value.per < data.value.industry_avg.per ? '✓ 저평가' : '✗ 고평가'
)
const pbrStatus = computed(() =>
  data.value && data.value.pbr < data.value.industry_avg.pbr ? '✓ 저평가' : '✗ 고평가'
)

// 판정 근거 tooltip. SFC에서는 일반 JS 문자열이라 \n이 안전하게 개행으로 동작.
const verdictBasis = computed(() => {
  const d = data.value
  if (!d) return ''
  const perAvg = d.industry_avg.per
  const pbrAvg = d.industry_avg.pbr
  const perLow = d.per < perAvg
  const pbrLow = d.pbr < pbrAvg
  return (
    '판정 규칙: PER·PBR이 모두 업계평균보다 낮으면 저평가, 모두 높으면 고평가, 그 외 중립\n\n' +
    'PER ' + d.per + ' vs 업계 ' + perAvg.toFixed(1) + ' → ' +
    (perLow ? '낮음(저평가 신호)' : '높음(고평가 신호)') + '\n' +
    'PBR ' + d.pbr + ' vs 업계 ' + pbrAvg.toFixed(2) + ' → ' +
    (pbrLow ? '낮음(저평가 신호)' : '높음(고평가 신호)') + '\n\n' +
    '→ 종합 판정: ' + d.verdict
  )
})
</script>

<template>
  <div class="card">
    <h2>💰 재무 분석 (이슈 002)</h2>
    <div v-if="error" class="error">재무 분석 로드 실패: {{ error }}</div>
    <div v-else-if="loading || !data" class="loading">분석 중...</div>
    <div v-else style="margin-top: 15px;">
      <div style="margin-bottom: 20px;">
        <strong style="font-size: 18px;">판정 결과</strong>
        <span class="tooltip-icon" :data-tooltip="verdictBasis">?</span>
        <div class="verdict-badge" :class="verdictClass" style="font-size: 16px;">
          {{ data.verdict }}
        </div>
        <div style="font-size: 12px; color: #7f8c8d; margin-top: 6px;">
          기준일: {{ data.as_of || '-' }}
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-box">
          <div class="metric-label">PER (주가수익비율)</div>
          <div class="metric-value">{{ data.per.toFixed(1) }}</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ data.industry_avg.per.toFixed(1) }} {{ perStatus }}
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">PBR (주가순자산비율)</div>
          <div class="metric-value">{{ data.pbr.toFixed(2) }}</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ data.industry_avg.pbr.toFixed(2) }} {{ pbrStatus }}
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">ROE (자기자본수익률)</div>
          <div class="metric-value">{{ data.roe.toFixed(1) }}%</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ data.industry_avg.roe.toFixed(1) }}%
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">배당수익률</div>
          <div class="metric-value">{{ data.dividend_yield.toFixed(2) }}%</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ data.industry_avg.dividend_yield.toFixed(2) }}%
          </div>
        </div>
      </div>

      <div class="comparison">
        <div class="comparison-card">
          <div class="comparison-title">📊 삼성전자 재무지표</div>
          <div style="font-size: 12px; line-height: 1.8; color: #495057;">
            <div>EPS: {{ data.eps.toLocaleString() }}원</div>
            <div>BPS: {{ data.bps.toLocaleString() }}원</div>
            <div>부채비율: {{ data.debt_ratio.toFixed(1) }}%</div>
          </div>
        </div>
        <div class="comparison-card">
          <div class="comparison-title">🏭 반도체 업계 평균</div>
          <div style="font-size: 12px; color: #7f8c8d;">
            <div>4개사 (SK하이닉스, DB하이텍, 주성엔지니어링, 원익IPS)</div>
            <div style="margin-top: 8px; color: #495057;">
              PER: {{ data.industry_avg.per.toFixed(1) }} | PBR: {{ data.industry_avg.pbr.toFixed(2) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
