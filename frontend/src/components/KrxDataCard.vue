<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode, currentName } from '../composables/useCurrentStock.js'

// 개요 탭 좌측: 기업 개요 + 핵심 지표 (overview + financial 조합)
const ov = useAsyncData(() => api.overview(currentCode.value))
const fin = useAsyncData(() => api.financial(currentCode.value))
onMounted(() => { ov.load(); fin.load() })
watch(currentCode, () => { ov.load(); fin.load() })

const o = computed(() => ov.data.value || {})
const f = computed(() => fin.data.value || {})

const change = computed(() => Number(o.value.change_rate ?? 0))
const changeClass = computed(() => (change.value > 0 ? 'value-up' : change.value < 0 ? 'value-down' : ''))
const changeText = computed(() => {
  const amt = o.value.change, rate = o.value.change_rate
  if (rate == null) return ''
  const sign = rate > 0 ? '+' : ''
  return `${sign}${Number(amt ?? 0).toLocaleString()} (${sign}${Number(rate).toFixed(2)}%)`
})

const num = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()
const n = (v, d = 1) => (v == null || isNaN(v)) ? '-' : Number(v).toFixed(d)
const cap = (v) => {
  if (v == null || isNaN(v)) return '-'
  if (v >= 1e12) return (v / 1e12).toFixed(1) + '조'
  if (v >= 1e8) return Math.round(v / 1e8).toLocaleString() + '억'
  return Number(v).toLocaleString()
}
const volM = (v) => (v == null || isNaN(v)) ? '-' : (v / 1e6).toFixed(1) + 'M'

const summaryText = computed(() => {
  if (o.value.summary) return o.value.summary
  const parts = []
  if (o.value.sector) parts.push(`업종: ${o.value.sector}`)
  parts.push('상세 기업 개요가 제공되지 않아 핵심 지표로 대체합니다.')
  return parts.join(' · ')
})
</script>

<template>
  <div class="col">
    <!-- 기업 개요 -->
    <div class="card">
      <div class="card-head">
        <span class="card-title">{{ currentName }} <span class="stock-code">{{ currentCode }}</span></span>
        <span v-if="o.sector" class="stock-pill sector">{{ o.sector }}</span>
      </div>
      <div v-if="ov.loading.value && !ov.data.value" class="loading">불러오는 중...</div>
      <template v-else>
        <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px;">
          <span class="stock-price">{{ num(o.current_price) }}</span>
          <span class="stock-change mono" :class="changeClass">{{ changeText }}</span>
        </div>
        <div class="overview-summary">{{ summaryText }}</div>
      </template>
    </div>

    <!-- 핵심 지표 -->
    <div class="card">
      <div class="card-title" style="margin-bottom: 12px;">핵심 지표</div>
      <div class="stat-grid">
        <div class="stat-cell"><div class="stat-label">시가총액</div><div class="stat-value">{{ cap(o.market_cap) }}</div></div>
        <div class="stat-cell"><div class="stat-label">PER</div><div class="stat-value">{{ n(f.per) }}</div></div>
        <div class="stat-cell"><div class="stat-label">PBR</div><div class="stat-value">{{ n(f.pbr, 2) }}</div></div>
        <div class="stat-cell"><div class="stat-label">ROE</div><div class="stat-value">{{ n(f.roe) }}%</div></div>
        <div class="stat-cell"><div class="stat-label">52주 최고</div><div class="stat-value">{{ num(o.week52_high) }}</div></div>
        <div class="stat-cell"><div class="stat-label">52주 최저</div><div class="stat-value">{{ num(o.week52_low) }}</div></div>
        <div class="stat-cell"><div class="stat-label">거래량</div><div class="stat-value">{{ volM(o.volume) }}</div></div>
        <div class="stat-cell"><div class="stat-label">외국인 비율</div><div class="stat-value">{{ o.foreign_ratio == null ? '-' : n(o.foreign_ratio) + '%' }}</div></div>
        <div class="stat-cell"><div class="stat-label">배당수익률</div><div class="stat-value">{{ n(f.dividend_yield, 2) }}%</div></div>
      </div>
      <div class="tx-mut" style="font-size: 11px; margin-top: 10px;">기준일 {{ o.as_of || '-' }}</div>
    </div>
  </div>
</template>
