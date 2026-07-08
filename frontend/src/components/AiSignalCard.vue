<script setup>
import { computed, onMounted, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

// 개요 탭 우측: AI 종합 시그널 미니 카드 (recommendation 기반)
const emit = defineEmits(['goto'])

const { data, error, loading, load } = useAsyncData(() => api.recommendation(currentCode.value))
onMounted(load)
watch(currentCode, load)

const grade = computed(() => data.value?.grade || 'hold')
const gradeKo = computed(() => (grade.value === 'buy' ? '매수' : grade.value === 'sell' ? '매도' : '관망'))
const gradeEn = computed(() => (grade.value === 'buy' ? 'BUY' : grade.value === 'sell' ? 'SELL' : 'HOLD'))
const txClass = computed(() => (grade.value === 'buy' ? 'tx-buy' : grade.value === 'sell' ? 'tx-sell' : 'tx-hold'))
const confidence = computed(() => data.value?.confidence ?? Math.round((data.value?.score ?? 0) * 100))

const upside = computed(() => {
  const c = data.value?.current_price, t = data.value?.target_price
  if (!c || t == null) return null
  return ((t - c) / c) * 100
})
const rr = computed(() => {
  const c = data.value?.current_price, t = data.value?.target_price, s = data.value?.stop_loss
  if (!c || t == null || s == null || c - s === 0) return null
  return (t - c) / (c - s)
})
const num = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()
</script>

<template>
  <div class="card signal-card">
    <div v-if="error" class="error">시그널 로드 실패</div>
    <div v-else-if="loading || !data" class="loading">분석 중...</div>
    <template v-else>
      <div class="mini-label">AI 종합 시그널</div>
      <div class="signal-verdict" :class="txClass">{{ gradeKo }}</div>
      <div class="signal-sub">{{ gradeEn }} · 신뢰도 {{ confidence }}%</div>
      <div class="divider"></div>
      <div class="signal-2x2">
        <div>
          <div class="mini-label tx-buy">목표가</div>
          <div class="mini-value">{{ num(data.target_price) }}</div>
        </div>
        <div>
          <div class="mini-label tx-sell">손절가</div>
          <div class="mini-value">{{ num(data.stop_loss) }}</div>
        </div>
        <div>
          <div class="mini-label">상승 여력</div>
          <div class="mini-value tx-buy">{{ upside == null ? '-' : (upside > 0 ? '+' : '') + upside.toFixed(1) + '%' }}</div>
        </div>
        <div>
          <div class="mini-label">손익비</div>
          <div class="mini-value tx-accent">{{ rr == null ? '-' : rr.toFixed(2) }}</div>
        </div>
      </div>
      <button class="cta-btn" @click="emit('goto', 'recommendation')">종합 추천 상세 보기</button>
    </template>
  </div>
</template>
