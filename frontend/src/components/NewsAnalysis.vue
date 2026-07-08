<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.news(currentCode.value))
onMounted(load)
watch(currentCode, load)

const headlines = computed(() => data.value?.headlines || [])

const sentimentLabel = computed(() => {
  const s = data.value?.sentiment
  return s === 'positive' ? '긍정적' : s === 'negative' ? '부정적' : '중립'
})
const sentimentClass = computed(() => {
  const s = data.value?.sentiment
  return s === 'positive' ? 'tx-buy' : s === 'negative' ? 'tx-sell' : 'tx-hold'
})

// 감성 점수 [-1,1] → 0~100 환산
const score100 = computed(() => {
  const s = data.value?.score
  return s == null ? null : Math.round(((s + 1) / 2) * 100)
})

// 호재/중립/악재 집계
const counts = computed(() => {
  const c = { pos: 0, neu: 0, neg: 0 }
  headlines.value.forEach((h) => {
    if (h.score > 0) c.pos++
    else if (h.score < 0) c.neg++
    else c.neu++
  })
  return c
})
const total = computed(() => headlines.value.length || 1)
const pct = (n) => Math.round((n / total.value) * 100)

// 선택된 뉴스(팝업)
const selected = ref(null)
function open(headline) { selected.value = headline }
function close() { selected.value = null }

function scoreChip(score) {
  if (score > 0) return { text: '호재', cls: 'sig-buy' }
  if (score < 0) return { text: '악재', cls: 'sig-sell' }
  return { text: '중립', cls: 'sig-hold' }
}
</script>

<template>
  <div v-if="error" class="card"><div class="error">뉴스 로드 실패: {{ error }}</div></div>
  <div v-else-if="loading || !data" class="card"><div class="loading">뉴스 수집 중...</div></div>
  <div v-else class="split wide-left">
    <!-- 뉴스 & 공시 -->
    <div class="card" style="padding: 0; overflow: hidden;">
      <div style="padding: 14px 16px; border-bottom: 1px solid var(--bd); display: flex; justify-content: space-between; align-items: center;">
        <span class="card-title">뉴스 &amp; 공시</span>
        <span class="tx-mut" style="font-size: 12px;">
          {{ data.article_count }}건 · {{ data.source === 'live' ? '실시간' : '캐시' }}
        </span>
      </div>
      <ul class="news-list" style="margin: 0;">
        <li v-for="(hl, idx) in headlines" :key="idx" class="news-item" style="padding: 13px 16px;" @click="open(hl)">
          <span class="sig-chip" :class="scoreChip(hl.score).cls">{{ scoreChip(hl.score).text }}</span>
          <span class="news-title" style="white-space: normal;">{{ hl.title }}</span>
          <span class="news-date">{{ hl.date }}</span>
        </li>
        <li v-if="!headlines.length" class="news-item" style="cursor: default;">
          <span class="tx-mut">수집된 뉴스가 없습니다.</span>
        </li>
      </ul>
    </div>

    <!-- 감성 분석 -->
    <div class="card">
      <div class="card-title" style="margin-bottom: 14px;">뉴스 감성 분석</div>
      <div class="news-score-block">
        <span class="news-big-score" :class="sentimentClass">{{ score100 == null ? '-' : score100 }}</span>
        <span class="tx-mut" style="font-size: 14px;">/100</span>
        <div :class="sentimentClass" style="font-size: 13px; font-weight: 600; margin-top: 2px;">{{ sentimentLabel }}</div>
      </div>

      <div class="score-item">
        <div class="score-row"><span>호재</span><span class="tx-buy mono">{{ counts.pos }} ({{ pct(counts.pos) }}%)</span></div>
        <div class="meter"><div class="meter-fill" :style="{ width: pct(counts.pos) + '%', background: 'var(--buy)' }"></div></div>
      </div>
      <div class="score-item">
        <div class="score-row"><span>중립</span><span class="tx-hold mono">{{ counts.neu }} ({{ pct(counts.neu) }}%)</span></div>
        <div class="meter"><div class="meter-fill" :style="{ width: pct(counts.neu) + '%', background: 'var(--hold)' }"></div></div>
      </div>
      <div class="score-item">
        <div class="score-row"><span>악재</span><span class="tx-sell mono">{{ counts.neg }} ({{ pct(counts.neg) }}%)</span></div>
        <div class="meter"><div class="meter-fill" :style="{ width: pct(counts.neg) + '%', background: 'var(--sell)' }"></div></div>
      </div>
    </div>
  </div>

  <!-- 팝업(모달) -->
  <div v-if="selected" class="modal-overlay" @click.self="close">
    <div class="modal">
      <button class="modal-close" @click="close" aria-label="닫기">×</button>
      <div class="modal-meta">
        {{ selected.source }} · {{ selected.date }}
        <span class="sig-chip" :class="scoreChip(selected.score).cls" style="margin-left: 6px;">
          {{ scoreChip(selected.score).text }} ({{ selected.score }})
        </span>
      </div>
      <h3 class="modal-title">{{ selected.title }}</h3>
      <div class="modal-body">
        <p v-if="selected.summary" class="modal-summary">{{ selected.summary }}</p>
        <p v-else class="modal-summary modal-summary-empty">
          이 기사의 본문 요약이 제공되지 않습니다. 아래 버튼으로 원문을 확인하세요.
        </p>
      </div>
      <a v-if="selected.url" :href="selected.url" target="_blank" rel="noopener" class="modal-cta">
        원문 전체 보기 ↗
      </a>
    </div>
  </div>
</template>
