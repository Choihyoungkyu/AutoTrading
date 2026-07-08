<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(
  () => api.priceTarget(currentCode.value)
)
onMounted(load)
watch(currentCode, load)

const pct = (v) => (v == null || isNaN(v)) ? '-' : Math.round(v * 100)
const won = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString() + '원'
const num = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()

// 목표가 출처: 증권사 컨센서스 평균 vs 커버리지 없어 기본 추정
const consensus = computed(() => data.value?.consensus || null)
const isConsensus = computed(() => data.value?.source === 'consensus' && !!consensus.value)

// 평균 투자의견(1~5, 높을수록 매수) → 라벨
const opinionLabel = computed(() => {
  const m = consensus.value?.recomm_mean
  if (m == null) return null
  if (m >= 4.5) return '적극 매수'
  if (m >= 3.5) return '매수'
  if (m >= 2.5) return '중립'
  if (m >= 1.5) return '매도'
  return '적극 매도'
})

// 지지·저항 사다리 좌표
const ladder = computed(() => {
  const d = data.value
  if (!d) return null
  const s = d.support || [], r = d.resistance || []
  const pts = [
    { label: '손절', v: d.stop_loss, color: 'var(--sell)', big: false },
    { label: 'S2', v: s[1], color: 'var(--down)', big: false },
    { label: 'S1', v: s[0], color: 'var(--down)', big: false },
    { label: '현재가', v: d.current_price, color: 'var(--accent)', big: true },
    { label: 'R1', v: r[0], color: 'var(--up)', big: false },
    { label: 'R2', v: r[1], color: 'var(--up)', big: false },
    { label: '목표', v: d.target_price, color: 'var(--buy)', big: false },
  ].filter((p) => p.v != null && !isNaN(p.v))
  if (pts.length < 2) return null
  const vals = pts.map((p) => p.v)
  const min = Math.min(...vals), max = Math.max(...vals)
  const span = max - min || 1
  pts.forEach((p) => { p.x = 40 + ((p.v - min) / span) * 920 })
  return { pts }
})

const chips = computed(() => {
  const d = data.value
  if (!d) return []
  const s = d.support || [], r = d.resistance || []
  return [
    { label: '손절가', v: d.stop_loss, cls: 'tx-sell' },
    { label: '지지 S1', v: s[0], cls: 'tx-down' },
    { label: '현재가', v: d.current_price, cls: 'tx-accent' },
    { label: '저항 R1', v: r[0], cls: 'tx-up' },
    { label: '목표가', v: d.target_price, cls: 'tx-buy' },
  ].filter((c) => c.v != null)
})

const scen = computed(() => data.value?.scenarios || null)
</script>

<template>
  <div v-if="error" class="card"><div class="error">목표가 로드 실패: {{ error }}</div></div>
  <div v-else-if="loading || !data" class="card"><div class="loading">계산 중...</div></div>
  <div v-else>
    <!-- 목표가 출처 배너 -->
    <div class="pt-source" :class="isConsensus ? 'is-consensus' : 'is-estimate'">
      <template v-if="isConsensus">
        📊 <b>증권사 컨센서스 평균 목표가</b>
        <span v-if="opinionLabel"> · 평균 투자의견 <b>{{ opinionLabel }}</b> ({{ consensus.recomm_mean }})</span>
        <span v-if="consensus.as_of" class="tx-mut"> · 기준 {{ consensus.as_of }}</span>
      </template>
      <template v-else>
        ⚠️ 이 종목은 증권사 목표가 컨센서스가 없어 <b>기본 추정치</b>(현재가 +{{ pct(data.expected_return) }}%)로 표시합니다.
      </template>
    </div>

    <!-- KPI 4카드 -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">현재가</div>
        <div class="kpi-value">{{ won(data.current_price) }}</div>
        <div class="kpi-note tx-mut">기준일 {{ data.as_of }}</div>
      </div>
      <div class="kpi-card buy">
        <div class="kpi-label">목표가</div>
        <div class="kpi-value">{{ won(data.target_price) }}</div>
        <div class="kpi-note">상승여력 +{{ data.upside != null ? Number(data.upside).toFixed(1) : pct(data.expected_return) }}%</div>
      </div>
      <div class="kpi-card sell">
        <div class="kpi-label">손절가</div>
        <div class="kpi-value">{{ won(data.stop_loss) }}</div>
        <div class="kpi-note">−{{ pct(data.max_loss) }}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">손익비 (R/R)</div>
        <div class="kpi-value tx-accent">{{ data.risk_reward_ratio ?? '-' }}</div>
        <div class="kpi-note tx-mut">위험 대비 보상</div>
      </div>
    </div>

    <!-- 지지·저항 구간 -->
    <div class="card" style="margin-top: 16px;">
      <div class="card-title" style="margin-bottom: 8px;">지지 · 저항 구간</div>
      <div v-if="ladder" class="ladder-wrap">
        <svg viewBox="0 0 1000 56" preserveAspectRatio="none" style="width: 100%; height: 100%;">
          <line x1="20" y1="28" x2="980" y2="28" stroke="var(--grid)" stroke-width="2" />
          <template v-for="p in ladder.pts" :key="p.label">
            <line :x1="p.x" y1="14" :x2="p.x" y2="42" :stroke="p.color" stroke-width="2" />
            <circle :cx="p.x" cy="28" :r="p.big ? 6 : 4" :fill="p.color" />
          </template>
        </svg>
      </div>
      <div v-else class="loading">지지·저항 데이터를 계산할 수 없습니다.</div>

      <div class="level-chips">
        <div v-for="c in chips" :key="c.label" class="level-chip">
          <div class="lc-label" :class="c.cls">{{ c.label }}</div>
          <div class="lc-value">{{ num(c.v) }}</div>
        </div>
      </div>
    </div>

    <!-- 시나리오 -->
    <div v-if="scen" class="scenario-grid" style="margin-top: 16px;">
      <div class="scenario-card buy">
        <div class="scenario-name tx-buy">낙관</div>
        <div class="scenario-price">{{ num(scen.optimistic.price) }}</div>
        <div class="scenario-desc">{{ scen.optimistic.desc }}</div>
      </div>
      <div class="scenario-card hold">
        <div class="scenario-name tx-hold">중립</div>
        <div class="scenario-price">{{ num(scen.neutral.price) }}</div>
        <div class="scenario-desc">{{ scen.neutral.desc }}</div>
      </div>
      <div class="scenario-card sell">
        <div class="scenario-name tx-sell">비관</div>
        <div class="scenario-price">{{ num(scen.pessimistic.price) }}</div>
        <div class="scenario-desc">{{ scen.pessimistic.desc }}</div>
      </div>
    </div>

    <!-- 산출 기준 -->
    <div class="card" style="margin-top: 16px;">
      <div class="tx-mut" style="font-size: 11px; line-height: 1.7;">
        <template v-if="isConsensus">
          목표가 = 증권사 컨센서스 평균 목표주가 · 손절가 = 현재가 ×(1−{{ pct(data.max_loss) }}%) 리스크 가드레일 · 지지/저항 = 피벗 포인트 계산
        </template>
        <template v-else>
          목표가 = 현재가 ×(1+{{ pct(data.expected_return) }}%) 추정 · 손절가 = 현재가 ×(1−{{ pct(data.max_loss) }}%) · 지지/저항 = 피벗 포인트 계산
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pt-source {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 16px;
}
.pt-source.is-consensus {
  background: var(--buy-bg, rgba(34, 197, 94, 0.1));
  color: var(--tx);
  border: 1px solid var(--buy);
}
.pt-source.is-estimate {
  background: var(--hold-bg, rgba(234, 179, 8, 0.1));
  color: var(--tx);
  border: 1px solid var(--hold);
}
</style>
