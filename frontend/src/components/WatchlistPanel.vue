<script setup>
import { ref, watch } from 'vue'
import { api } from '../api/client.js'
import { watchlist } from '../composables/useWatchlist.js'
import { setStock } from '../composables/useCurrentStock.js'

// 홈 화면 지수 밑: 관심 종목별 현재가·등락률. 클릭 시 해당 종목으로 이동.
const quotes = ref({})   // code -> { price, changeRate, name }

async function loadQuotes() {
  const results = await Promise.all(
    watchlist.value.map(async (s) => {
      const q = await api.quote(s.code)
      return [s.code, q && !q.error ? q : null]
    })
  )
  quotes.value = Object.fromEntries(results)
}

// 관심 종목이 바뀌면(추가/제거) 시세를 다시 불러온다.
watch(watchlist, loadQuotes, { deep: true, immediate: true })

function fmtPrice(v) {
  return Number(v).toLocaleString('ko-KR')
}
function fmtRate(v) {
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`
}
function dir(rate) {
  if (rate > 0) return 'up'
  if (rate < 0) return 'down'
  return 'flat'
}
</script>

<template>
  <section class="watchlist">
    <h3 class="watchlist-title">⭐ 관심 종목</h3>
    <div v-if="!watchlist.length" class="watchlist-empty">
      종목 상세 화면에서 하트(🤍)를 눌러 관심 종목을 추가하세요.
    </div>
    <div v-else class="watchlist-grid">
      <button
        v-for="s in watchlist"
        :key="s.code"
        class="watch-item"
        :class="dir(quotes[s.code]?.changeRate)"
        @click="setStock(s.code, quotes[s.code]?.name || s.name)"
      >
        <span class="watch-name">{{ quotes[s.code]?.name || s.name }}</span>
        <template v-if="quotes[s.code]">
          <span class="watch-price">{{ fmtPrice(quotes[s.code].price) }}</span>
          <span class="watch-rate">{{ fmtRate(quotes[s.code].changeRate) }}</span>
        </template>
        <span v-else class="watch-rate muted">조회 실패</span>
      </button>
    </div>
  </section>
</template>
