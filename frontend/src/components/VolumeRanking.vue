<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '../api/client.js'
import { setStock } from '../composables/useCurrentStock.js'

// 거래량 상위 종목 + 기술적 평가(5단계). 행 클릭 시 해당 종목 상세로 이동.
// market prop으로 KOSPI/KOSDAQ 시장을 전환한다.
const props = defineProps({
  market: { type: String, default: 'KOSPI' },
})

const loading = ref(true)
const error = ref('')
const stocks = ref([])

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.topVolume(props.market)
    if (res && res.error) {
      error.value = res.error
    } else {
      stocks.value = (res && res.stocks) || []
    }
  } catch (e) {
    error.value = '데이터를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.market, load)

function fmtPrice(v) {
  return v == null ? '-' : Number(v).toLocaleString('ko-KR')
}
function fmtRate(v) {
  if (v == null) return '-'
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`
}
function fmtVolume(v) {
  if (v == null) return '-'
  return Number(v).toLocaleString('ko-KR') + '주'
}
function dir(rate) {
  if (rate > 0) return 'up'
  if (rate < 0) return 'down'
  return 'flat'
}
</script>

<template>
  <div class="ranking">
    <h1 class="section-title">🔥 {{ market }} 거래량 상위</h1>
    <p class="ranking-note">
      거래량 순위 · 현재가 · 등락률 · 거래량. 종목을 누르면 상세 분석으로 이동합니다.
    </p>

    <div v-if="loading" class="ranking-msg">분석 중… 잠시만 기다려 주세요.</div>
    <div v-else-if="error" class="ranking-msg error">{{ error }}</div>

    <div v-else class="vr-list">
      <button
        v-for="s in stocks"
        :key="s.code"
        type="button"
        class="vr-item"
        @click="setStock(s.code, s.name)"
      >
        <span class="vr-rank">{{ s.rank }}</span>
        <span class="vr-info">
          <span class="vr-name">{{ s.name }}</span>
          <span class="vr-code">{{ s.code }}</span>
        </span>
        <span class="vr-price-box">
          <span class="vr-price">{{ fmtPrice(s.price) }}</span>
          <span class="vr-rate" :class="'value-' + dir(s.changeRate)">{{ fmtRate(s.changeRate) }}</span>
          <span class="vr-vol">거래량 {{ fmtVolume(s.volume) }}</span>
        </span>
      </button>
      <p class="ranking-count">총 {{ stocks.length }}개 종목</p>
    </div>
  </div>
</template>

<style scoped>
.ranking-note {
  font-size: 13px;
  color: var(--mut);
  line-height: 1.5;
  margin-bottom: 16px;
}
.ranking-msg {
  padding: 40px 16px;
  text-align: center;
  color: var(--mut);
}
.ranking-msg.error { color: var(--sell); }

/* 반응형 리스트: 가로 스크롤 없이 모든 폭에서 자연스럽게 흐른다 */
.vr-list { display: flex; flex-direction: column; }
.vr-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 6px;
  border: none;
  border-bottom: 1px solid var(--bd);
  background: transparent;
  color: var(--tx);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.vr-item:hover { background: var(--hover); }

.vr-rank {
  flex: none;
  width: 24px;
  text-align: center;
  font-size: 12px;
  color: var(--mut);
  font-variant-numeric: tabular-nums;
}

.vr-info { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.vr-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--tx);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vr-code { font-size: 11px; color: var(--mut); font-family: var(--mono); }

.vr-price-box { flex: none; display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.vr-price { font-size: 13px; font-weight: 600; font-family: var(--mono); color: var(--tx); }
.vr-rate { font-size: 12px; font-family: var(--mono); }
.vr-vol { font-size: 10px; color: var(--mut); font-family: var(--mono); }
.value-up { color: var(--up); }
.value-down { color: var(--down); }

.ranking-count { margin-top: 12px; font-size: 12px; color: var(--mut); }

/* 태블릿·데스크탑 */
@media (min-width: 768px) {
  .ranking-note { font-size: 14px; }
  .vr-item { gap: 14px; padding: 12px 10px; }
  .vr-rank { width: 32px; font-size: 13px; }
  .vr-info { flex-direction: row; align-items: baseline; gap: 10px; }
  .vr-name { font-size: 15px; }
  .vr-code { font-size: 12px; }
  .vr-price { font-size: 14px; }
  .vr-rate { font-size: 13px; }
  .vr-vol { font-size: 11px; }
}
</style>
