<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const expectedReturn = ref(0.15)
const maxLoss = ref(0.10)

const { data, error, loading, load } = useAsyncData(
  () => api.priceTarget(expectedReturn.value, maxLoss.value, currentCode.value)
)
onMounted(load)
watch(currentCode, load)

const pct = (v) => (v == null || isNaN(v)) ? '-' : Math.round(v * 100)
const won = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString() + '원'
const num = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()

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

    <!-- 슬라이더 -->
    <div class="card" style="margin-top: 16px;">
      <div class="pt-controls">
        <label>
          기대수익률: <strong class="tx-buy">{{ pct(expectedReturn) }}%</strong>
          <input type="range" min="0.05" max="0.5" step="0.05" v-model.number="expectedReturn" @change="load" />
        </label>
        <label>
          최대손실률: <strong class="tx-sell">{{ pct(maxLoss) }}%</strong>
          <input type="range" min="0.05" max="0.3" step="0.05" v-model.number="maxLoss" @change="load" />
        </label>
      </div>
      <div class="tx-mut" style="font-size: 11px; margin-top: 12px;">
        목표가 = 현재가 ×(1+기대수익률) · 손절가 = 현재가 ×(1−최대손실률) · 지지/저항 = 피벗 포인트 계산
      </div>
    </div>
  </div>
</template>
