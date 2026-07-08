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
const annual = computed(() => data.value?.annual || [])
const hasIndustry = computed(() => !!data.value?.industry_avg)

const verdictChip = computed(() => {
  const v = data.value?.verdict
  return v === '저평가' ? 'sig-buy' : v === '고평가' ? 'sig-sell' : 'sig-hold'
})

const n = (v, d = 1) => (v == null || isNaN(v)) ? '-' : Number(v).toFixed(d)
const won = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()
const jo = (v) => (v == null || isNaN(v)) ? '-' : (v / 1e12).toFixed(2) // 조원

// 매출 기준 최댓값(추이 막대 스케일)
const maxRevenue = computed(() => Math.max(1, ...annual.value.map((a) => Math.abs(a.revenue || 0))))
const barPct = (v) => Math.max(0, Math.min(100, (Math.abs(v || 0) / maxRevenue.value) * 100))

const perStatus = computed(() =>
  hasIndustry.value ? (data.value.per < data.value.industry_avg.per ? '✓ 저평가' : '✗ 고평가') : ''
)
const pbrStatus = computed(() =>
  hasIndustry.value ? (data.value.pbr < data.value.industry_avg.pbr ? '✓ 저평가' : '✗ 고평가') : ''
)

// 순위비율(percentile) 판단 근거 — KRX 밸류업 방식(업종 내 상대평가)
const valuation = computed(() => data.value?.valuation || null)

const verdictBasis = computed(() => {
  const d = data.value
  if (!d) return ''
  if (!hasIndustry.value) return '업종/업계평균을 불러오지 못해 저평가·고평가를 판정할 수 없습니다.'
  const perLow = d.per < d.industry_avg.per
  const pbrLow = d.pbr < d.industry_avg.pbr
  return (
    'PER ' + d.per + ' vs 업계 ' + d.industry_avg.per.toFixed(1) +
    ' → ' + (perLow ? '낮음(저평가 신호)' : '높음(고평가 신호)') + ' · ' +
    'PBR ' + d.pbr + ' vs 업계 ' + d.industry_avg.pbr.toFixed(2) +
    ' → ' + (pbrLow ? '낮음(저평가 신호)' : '높음(고평가 신호)')
  )
})

// 지표별 순위비율 점수(0~100, 높을수록 우수). 없는 지표는 제외.
const rankRows = computed(() => {
  const c = valuation.value?.components
  if (!c) return []
  const meta = [
    { key: 'per', label: 'PER', note: '낮을수록↑' },
    { key: 'pbr', label: 'PBR', note: '낮을수록↑' },
    { key: 'roe', label: 'ROE', note: '높을수록↑' },
    { key: 'dividend_yield', label: '배당수익률', note: '높을수록↑' },
  ]
  return meta
    .filter((m) => c[m.key] != null)
    .map((m) => ({ ...m, score: c[m.key] }))
})
const scoreColor = (s) => (s >= 60 ? 'var(--buy)' : s <= 40 ? 'var(--sell)' : 'var(--text-muted)')
</script>

<template>
  <div v-if="error" class="card"><div class="error">재무 분석 로드 실패: {{ error }}</div></div>
  <div v-else-if="loading || !data" class="card"><div class="loading">분석 중...</div></div>
  <div v-else-if="!hasAsOf" class="card">
    <div class="error">기준일 정보가 없어 신뢰할 수 없는 데이터입니다.</div>
  </div>
  <div v-else>
    <!-- 판정 배너 -->
    <div class="card">
      <div class="card-head">
        <span class="card-title">밸류에이션 판정</span>
        <span class="sig-chip" :class="verdictChip">{{ data.verdict }}</span>
      </div>
      <div class="overview-summary">{{ verdictBasis }}</div>

      <!-- 판단 근거: 업종 내 순위비율(KRX 밸류업 방식) -->
      <div v-if="rankRows.length" class="rank-basis">
        <div class="rank-basis-head">
          <span>업종 내 순위비율 판단 근거</span>
          <span v-if="valuation?.score != null" class="rank-total">
            종합 {{ valuation.score }}점
            <span class="tx-mut">/ 100 · {{ valuation.peer_count }}개사 비교</span>
          </span>
        </div>
        <div v-for="r in rankRows" :key="r.key" class="rank-row">
          <span class="rank-label">{{ r.label }} <span class="tx-mut">{{ r.note }}</span></span>
          <span class="rank-bar-track">
            <span class="rank-bar-fill" :style="{ width: r.score + '%', background: scoreColor(r.score) }"></span>
          </span>
          <span class="rank-score" :style="{ color: scoreColor(r.score) }">{{ r.score }}점</span>
        </div>
        <div class="tx-mut rank-hint">50점 = 업종 중위, 60점↑ 저평가·40점↓ 고평가 (PER·PBR 기준)</div>
      </div>

      <div class="tx-mut" style="font-size: 12px; margin-top: 8px;">기준일: {{ data.as_of }}</div>
    </div>

    <!-- 연간 실적 + 추이 -->
    <div class="split fin">
      <div class="card">
        <div class="card-head">
          <span class="card-title">연간 실적</span>
          <span class="unit-note">(단위: 조원)</span>
        </div>
        <table v-if="annual.length" class="data-table">
          <thead>
            <tr>
              <th>항목</th>
              <th v-for="a in annual" :key="a.year" style="text-align: right;">{{ a.year }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>매출액</td>
              <td v-for="a in annual" :key="a.year" style="text-align: right;">{{ jo(a.revenue) }}</td>
            </tr>
            <tr>
              <td>영업이익</td>
              <td v-for="a in annual" :key="a.year" style="text-align: right;"
                  :class="{ 'value-down': a.operating_income < 0 }">{{ jo(a.operating_income) }}</td>
            </tr>
            <tr>
              <td>순이익</td>
              <td v-for="a in annual" :key="a.year" style="text-align: right;"
                  :class="{ 'value-down': a.net_income < 0 }">{{ jo(a.net_income) }}</td>
            </tr>
            <tr>
              <td>영업이익률</td>
              <td v-for="a in annual" :key="a.year" style="text-align: right;">{{ n(a.operating_margin) }}%</td>
            </tr>
            <tr>
              <td>순이익률</td>
              <td v-for="a in annual" :key="a.year" style="text-align: right;">{{ n(a.net_margin) }}%</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="loading">이 종목의 연간 재무제표(매출·이익)는 현재 제공되지 않습니다.</div>
      </div>

      <div class="card">
        <div class="card-head">
          <span class="card-title">매출·영업이익 추이</span>
          <span v-if="annual.length" class="chart-legend">
            <span class="lg"><span class="sw" style="background: var(--secondary);"></span>매출</span>
            <span class="lg"><span class="sw" style="background: var(--buy);"></span>영업이익</span>
          </span>
        </div>
        <div v-if="annual.length" class="mini-chart"
             style="display: flex; align-items: flex-end; gap: 14px; height: 170px; padding-top: 8px;">
          <div v-for="a in annual" :key="a.year"
               style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; justify-content: flex-end;">
            <div style="display: flex; align-items: flex-end; gap: 4px; height: 130px;">
              <div :style="{ height: barPct(a.revenue) + '%', width: '16px', background: 'var(--secondary)', borderRadius: '3px 3px 0 0' }"></div>
              <div :style="{ height: barPct(a.operating_income) + '%', width: '16px', background: 'var(--buy)', borderRadius: '3px 3px 0 0' }"></div>
            </div>
            <div class="tx-mut" style="font-size: 11px; font-family: var(--mono);">{{ a.year }}</div>
          </div>
        </div>
        <div v-else class="loading">추이를 표시할 연간 데이터가 없습니다.</div>
      </div>
    </div>

    <!-- 재무 비율 & 밸류에이션 -->
    <div class="card">
      <div class="card-title" style="margin-bottom: 12px;">재무 비율 &amp; 밸류에이션</div>
      <div class="stat-grid cols4">
        <div class="stat-cell"><div class="stat-label">PER</div><div class="stat-value">{{ n(data.per) }}</div></div>
        <div class="stat-cell"><div class="stat-label">PBR</div><div class="stat-value">{{ n(data.pbr, 2) }}</div></div>
        <div class="stat-cell"><div class="stat-label">ROE</div><div class="stat-value tx-buy">{{ n(data.roe) }}%</div></div>
        <div class="stat-cell"><div class="stat-label">부채비율</div><div class="stat-value">{{ n(data.debt_ratio) }}%</div></div>
        <div class="stat-cell"><div class="stat-label">EPS</div><div class="stat-value">{{ won(data.eps) }}</div></div>
        <div class="stat-cell"><div class="stat-label">BPS</div><div class="stat-value">{{ won(data.bps) }}</div></div>
        <div class="stat-cell"><div class="stat-label">배당수익률</div><div class="stat-value">{{ n(data.dividend_yield, 2) }}%</div></div>
        <div class="stat-cell"><div class="stat-label">유보율</div><div class="stat-value">{{ data.retention_ratio == null ? '-' : n(data.retention_ratio) + '%' }}</div></div>
      </div>

      <div v-if="hasIndustry" class="tx-mut" style="font-size: 12px; margin-top: 12px; line-height: 1.7;">
        🏭 {{ data.industry_name }} · 동일업종 {{ data.industry_avg.peer_count }}개사 중앙값 —
        PER {{ n(data.industry_avg.per) }} {{ perStatus }} ·
        PBR {{ n(data.industry_avg.pbr, 2) }} {{ pbrStatus }} ·
        ROE {{ n(data.industry_avg.roe) }}%
      </div>
    </div>
  </div>
</template>

<style scoped>
.rank-basis {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border, #e5e7eb);
}
.rank-basis-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
}
.rank-total {
  font-family: var(--mono);
  font-size: 14px;
}
.rank-total .tx-mut {
  font-weight: 400;
  font-size: 11px;
}
.rank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.rank-label {
  flex: 0 0 auto;
  width: 92px;
  font-size: 12px;
}
.rank-label .tx-mut {
  font-size: 10px;
}
.rank-bar-track {
  flex: 1 1 auto;
  height: 8px;
  border-radius: 4px;
  background: var(--surface-2, #f1f5f9);
  overflow: hidden;
}
.rank-bar-fill {
  display: block;
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}
.rank-score {
  flex: 0 0 auto;
  width: 44px;
  text-align: right;
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 600;
}
.rank-hint {
  font-size: 11px;
  margin-top: 6px;
}

/* 태블릿·데스크탑: 라벨 여유 폭 */
@media (min-width: 768px) {
  .rank-label { width: 108px; font-size: 13px; }
}
</style>
