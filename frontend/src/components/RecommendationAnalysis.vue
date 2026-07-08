<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.recommendation(currentCode.value))
onMounted(load)
watch(currentCode, load)

const grade = computed(() => data.value?.grade || 'hold')
const gradeKo = computed(() => (grade.value === 'buy' ? '매수' : grade.value === 'sell' ? '매도' : '관망'))
const gradeEn = computed(() => (grade.value === 'buy' ? 'BUY' : grade.value === 'sell' ? 'SELL' : 'HOLD'))
const heroClass = computed(() => (grade.value === 'buy' ? 'buy' : grade.value === 'sell' ? 'sell' : 'hold'))
const txClass = computed(() => (grade.value === 'buy' ? 'tx-buy' : grade.value === 'sell' ? 'tx-sell' : 'tx-hold'))

const confidence = computed(() => data.value?.confidence ?? Math.round((data.value?.score ?? 0) * 100))
const factors = computed(() => data.value?.factors || [])
const dims = computed(() => data.value?.dimensions || [])

// 점수 막대 색 (디자인 로직)
const barColor = (s) => (s >= 75 ? 'var(--buy)' : s >= 55 ? 'var(--secondary)' : 'var(--hold)')
const sigChipCls = (s) => (s === 'buy' ? 'sig-buy' : s === 'sell' ? 'sig-sell' : 'sig-hold')
const num = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()
</script>

<template>
  <div v-if="error" class="card"><div class="error">추천 로드 실패: {{ error }}</div></div>
  <div v-else-if="loading || !data" class="card"><div class="loading">종합 분석 중...</div></div>
  <div v-else>
    <!-- Hero -->
    <div class="reco-hero" :class="heroClass">
      <div class="reco-eyebrow">AI 종합 시그널</div>
      <div class="reco-verdict-huge" :class="txClass">{{ gradeKo }}</div>
      <div class="reco-en" :class="txClass">{{ gradeEn }}</div>

      <div class="reco-conf">
        <div class="score-row"><span>신뢰도</span><span class="mono" :class="txClass">{{ confidence }}%</span></div>
        <div class="meter"><div class="meter-fill" :style="{ width: confidence + '%', background: 'var(--' + heroClass + ')' }"></div></div>
      </div>

      <div class="reco-pills">
        <div class="reco-pill">
          <div class="rp-label">현재가</div>
          <div class="rp-value">{{ num(data.current_price) }}</div>
        </div>
        <div class="reco-pill">
          <div class="rp-label tx-buy">목표가</div>
          <div class="rp-value tx-buy">{{ num(data.target_price) }}</div>
        </div>
        <div class="reco-pill">
          <div class="rp-label tx-sell">손절가</div>
          <div class="rp-value tx-sell">{{ num(data.stop_loss) }}</div>
        </div>
      </div>

      <div v-if="data.reasoning" class="reco-rationale">{{ data.reasoning }}</div>
    </div>

    <!-- 평가 요인별 점수 -->
    <div class="card" style="margin-top: 16px;">
      <div class="card-title" style="margin-bottom: 16px;">평가 요인별 점수</div>
      <div v-for="f in factors" :key="f.name" class="score-item">
        <div class="score-row">
          <span>{{ f.name }}</span>
          <span class="mono" style="font-weight: 700;" :style="{ color: barColor(f.score) }">{{ f.score }}</span>
        </div>
        <div class="meter"><div class="meter-fill" :style="{ width: f.score + '%', background: barColor(f.score) }"></div></div>
      </div>
    </div>

    <!-- 차원 요약 -->
    <div class="dim-grid">
      <div v-for="d in dims" :key="d.name" class="dim-card">
        <div class="dim-head">
          <span class="dim-name">{{ d.name }}</span>
          <span class="sig-chip" :class="sigChipCls(d.signal)">{{ d.tag }}</span>
        </div>
        <div class="dim-desc">{{ d.desc }}</div>
      </div>
    </div>
  </div>
</template>
