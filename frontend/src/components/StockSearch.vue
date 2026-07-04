<script setup>
import { ref } from 'vue'
import { api } from '../api/client.js'
import { setStock } from '../composables/useCurrentStock.js'

// 종목명/코드 검색 → 선택 시 상세 대시보드로 전환(setStock).
// 홈 화면(큰 검색창)과 헤더(작은 검색창)에서 공용으로 쓴다.
defineProps({
  placeholder: { type: String, default: '종목명 또는 코드 검색 (예: 하이닉스, 000660)' },
})

const query = ref('')
const results = ref([])
const open = ref(false)
let timer = null

function onInput() {
  open.value = true
  clearTimeout(timer)
  const q = query.value.trim()
  if (!q) { results.value = []; return }
  // 디바운스 250ms
  timer = setTimeout(async () => {
    const res = await api.search(q)
    results.value = Array.isArray(res) ? res : []
  }, 250)
}

function pick(item) {
  setStock(item.code, item.name)
  query.value = ''
  results.value = []
  open.value = false
}

function onEnter() {
  const q = query.value.trim()
  // 6자리 숫자 코드는 바로 조회
  if (/^\d{6}$/.test(q)) {
    setStock(q, q)
    query.value = ''
    results.value = []
    open.value = false
  } else if (results.value.length) {
    pick(results.value[0])
  }
}

// 드롭다운 바깥 클릭 시 닫기(블러 지연으로 클릭 이벤트 우선)
function onBlur() {
  setTimeout(() => { open.value = false }, 150)
}
</script>

<template>
  <div class="search-box">
    <input
      v-model="query"
      class="search-input"
      type="text"
      :placeholder="placeholder"
      @input="onInput"
      @focus="open = true"
      @blur="onBlur"
      @keyup.enter="onEnter"
    />
    <ul v-if="open && results.length" class="search-results">
      <li
        v-for="item in results"
        :key="item.code"
        class="search-result"
        @mousedown.prevent="pick(item)"
      >
        <span class="search-name">{{ item.name }}</span>
        <span class="search-meta">{{ item.code }} · {{ item.market }}</span>
      </li>
    </ul>
  </div>
</template>
