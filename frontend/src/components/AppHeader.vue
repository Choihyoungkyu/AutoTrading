<script setup>
import { computed, onMounted, ref } from 'vue'
import { useHealth } from '../composables/useStock.js'
import { api } from '../api/client.js'
import { currentCode, currentName, setStock } from '../composables/useCurrentStock.js'

const { data, error, ensureLoaded } = useHealth()
onMounted(ensureLoaded)

const dbText = computed(() => {
  if (error.value) return '✗ 오류'
  if (!data.value) return '연결 중...'
  return data.value.status === 'ok' ? '✓ 정상 연결' : '✗ 연결 실패'
})
const dbColor = computed(() => {
  if (!data.value || error.value) return error.value ? '#e74c3c' : ''
  return data.value.status === 'ok' ? '#27ae60' : '#e74c3c'
})

// --- 종목 검색 (네이버 자동완성) ---
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
  <header>
    <h1>📈 주식 분석 시스템 v1.0</h1>
    <p>PYKRX와 yfinance를 기반으로 한 다중 종목 분석 플랫폼</p>

    <div class="search-box">
      <input
        v-model="query"
        class="search-input"
        type="text"
        placeholder="종목명 또는 코드 검색 (예: 하이닉스, 000660)"
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

    <div class="status">
      <div class="status-item">
        <span class="status-badge">현재 종목</span>
        <span><strong>{{ currentName }}</strong> ({{ currentCode }})</span>
      </div>
      <div class="status-item">
        <span class="status-badge">데이터베이스</span>
        <span :style="{ color: dbColor }">{{ dbText }}</span>
      </div>
      <div class="status-item">
        <span class="status-badge">API Server</span>
        <span>http://localhost:8000</span>
      </div>
    </div>
  </header>
</template>
