<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode, currentName } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.financial(currentCode.value))
onMounted(load)
watch(currentCode, load)

// 기준일(as_of)이 없으면 신뢰할 수 없는 데이터로 보고 표시하지 않는다.
const hasAsOf = computed(() => !!data.value?.as_of)

const verdictClass = computed(() => {
  const v = data.value?.verdict
  return 'verdict-' + (v === '저평가' ? 'undervalued' : v === '고평가' ? 'overvalued' : 'neutral')
})

// 업종/업계평균 조회 성공 여부. 실패 시 비교 대신 "조회 실패"를 표시한다.
const hasIndustry = computed(() => !!data.value?.industry_avg)

const perStatus = computed(() =>
  hasIndustry.value && data.value.per < data.value.industry_avg.per ? '✓ 저평가' : hasIndustry.value ? '✗ 고평가' : ''
)
const pbrStatus = computed(() =>
  hasIndustry.value && data.value.pbr < data.value.industry_avg.pbr ? '✓ 저평가' : hasIndustry.value ? '✗ 고평가' : ''
)

// 판정 근거 tooltip. SFC에서는 일반 JS 문자열이라 \n이 안전하게 개행으로 동작.
const verdictBasis = computed(() => {
  const d = data.value
  if (!d) return ''
  if (!hasIndustry.value) return '업종/업계평균을 불러오지 못해 저평가·고평가를 판정할 수 없습니다.'
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
    <div v-else-if="!hasAsOf" class="error">
      기준일 정보가 없어 신뢰할 수 없는 데이터입니다. 표시하지 않습니다.
    </div>
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
            업계평균: {{ hasIndustry ? data.industry_avg.per.toFixed(1) + ' ' + perStatus : '조회 실패' }}
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">PBR (주가순자산비율)</div>
          <div class="metric-value">{{ data.pbr.toFixed(2) }}</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ hasIndustry ? data.industry_avg.pbr.toFixed(2) + ' ' + pbrStatus : '조회 실패' }}
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">ROE (자기자본수익률)</div>
          <div class="metric-value">{{ data.roe.toFixed(1) }}%</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ hasIndustry ? data.industry_avg.roe.toFixed(1) + '%' : '조회 실패' }}
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">배당수익률</div>
          <div class="metric-value">{{ data.dividend_yield.toFixed(2) }}%</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            업계평균: {{ hasIndustry ? data.industry_avg.dividend_yield.toFixed(2) + '%' : '조회 실패' }}
          </div>
        </div>
      </div>

      <div class="comparison">
        <div class="comparison-card">
          <div class="comparison-title">📊 {{ currentName }} 재무지표</div>
          <div style="font-size: 12px; line-height: 1.8; color: #495057;">
            <div>EPS: {{ data.eps.toLocaleString() }}원</div>
            <div>BPS: {{ data.bps.toLocaleString() }}원</div>
            <div>부채비율: {{ data.debt_ratio.toFixed(1) }}%</div>
          </div>
        </div>
        <div class="comparison-card">
          <div class="comparison-title">🏭 {{ hasIndustry ? data.industry_name + ' 업계 평균' : '업계 평균' }}</div>
          <div style="font-size: 12px; color: #7f8c8d;">
            <template v-if="hasIndustry">
              <div>동일업종 {{ data.industry_avg.peer_count }}개사 중앙값</div>
              <div style="margin-top: 8px; color: #495057;">
                PER: {{ data.industry_avg.per.toFixed(1) }} | PBR: {{ data.industry_avg.pbr.toFixed(2) }}
              </div>
            </template>
            <div v-else style="color: #e74c3c;">조회 실패</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
