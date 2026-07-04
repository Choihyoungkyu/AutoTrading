import { ref, watch } from 'vue'

// 관심 종목: localStorage에 저장해 새로고침/재방문 시에도 유지한다.
// 항목 형태: { code, name }
const KEY = 'watchlist'

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY))
    return Array.isArray(raw) ? raw : []
  } catch {
    return []
  }
}

export const watchlist = ref(load())

watch(watchlist, (v) => localStorage.setItem(KEY, JSON.stringify(v)), { deep: true })

export function isFavorite(code) {
  return watchlist.value.some((s) => s.code === code)
}

export function toggleFavorite(code, name) {
  const i = watchlist.value.findIndex((s) => s.code === code)
  if (i >= 0) {
    watchlist.value.splice(i, 1)
  } else {
    watchlist.value.push({ code, name: name || code })
  }
}
