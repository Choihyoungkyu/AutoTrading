<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.news(currentCode.value))
onMounted(load)
watch(currentCode, load)

const sentimentLabel = computed(() => {
  const s = data.value?.sentiment
  return s === 'positive' ? '호재' : s === 'negative' ? '악재' : '중립'
})
const sentimentClass = computed(() => {
  const s = data.value?.sentiment
  return 'verdict-' + (s === 'positive' ? 'undervalued' : s === 'negative' ? 'overvalued' : 'neutral')
})

// 선택된 뉴스(팝업). null이면 팝업 닫힘.
const selected = ref(null)
function open(headline) { selected.value = headline }
function close() { selected.value = null }

function scoreTag(score) {
  if (score > 0) return { text: '호재', cls: 'news-tag-pos' }
  if (score < 0) return { text: '악재', cls: 'news-tag-neg' }
  return { text: '중립', cls: 'news-tag-neu' }
}
</script>

<template>
  <div class="card">
    <h2>📰 뉴스 분석 (이슈 004)</h2>
    <div v-if="error" class="error">뉴스 로드 실패: {{ error }}</div>
    <div v-else-if="loading || !data" class="loading">뉴스 수집 중...</div>
    <div v-else>
      <div style="margin-bottom: 15px;">
        <strong style="font-size: 16px;">시장 심리</strong>
        <span class="verdict-badge" :class="sentimentClass">{{ sentimentLabel }}</span>
        <div style="font-size: 12px; color: #7f8c8d; margin-top: 6px;">
          점수 {{ data.score }} · 기사 {{ data.article_count }}건 · 기준일 {{ data.as_of }}
          · 출처 {{ data.source === 'live' ? '실시간' : '캐시' }}
        </div>
      </div>

      <!-- 제목만 노출하는 게시글 목록. 클릭 시 팝업 -->
      <ul class="news-list">
        <li
          v-for="(hl, idx) in data.headlines"
          :key="idx"
          class="news-item"
          @click="open(hl)"
        >
          <span class="news-tag" :class="scoreTag(hl.score).cls">{{ scoreTag(hl.score).text }}</span>
          <span class="news-title">{{ hl.title }}</span>
          <span class="news-date">{{ hl.date }}</span>
        </li>
      </ul>
    </div>

    <!-- 팝업(모달): 클릭한 뉴스를 표시 -->
    <div v-if="selected" class="modal-overlay" @click.self="close">
      <div class="modal">
        <button class="modal-close" @click="close" aria-label="닫기">×</button>
        <div class="modal-meta">
          {{ selected.source }} · {{ selected.date }}
          <span class="news-tag" :class="scoreTag(selected.score).cls" style="margin-left:6px;">
            {{ scoreTag(selected.score).text }} ({{ selected.score }})
          </span>
        </div>
        <h3 class="modal-title">{{ selected.title }}</h3>
        <div class="modal-body">
          <p v-if="selected.summary" class="modal-summary">{{ selected.summary }}</p>
          <p v-else class="modal-summary modal-summary-empty">
            이 기사의 본문 요약이 제공되지 않습니다. 아래 버튼으로 원문을 확인하세요.
          </p>
        </div>
        <a
          v-if="selected.url"
          :href="selected.url"
          target="_blank"
          rel="noopener"
          class="modal-cta"
        >
          원문 전체 보기 ↗
        </a>
      </div>
    </div>
  </div>
</template>
