import { ref, watch } from 'vue'
import { api } from '../api/client.js'
import { currentCode } from './useCurrentStock.js'

// 여러 컴포넌트가 같은 엔드포인트를 공유하므로(예: 현재가 카드 + 시세 표),
// 모듈 레벨 싱글턴으로 만들어 중복 호출을 막는다.

function createResource(loader) {
  const data = ref(null)
  const error = ref(null)
  const loading = ref(true)
  let started = false

  async function load() {
    loading.value = true
    error.value = null
    try {
      const result = await loader()
      if (result && result.error) {
        error.value = result.error
        data.value = null
      } else {
        data.value = result
      }
    } catch (e) {
      error.value = e.message
      data.value = null
    } finally {
      loading.value = false
    }
  }

  // 최초 1회만 자동 로드(여러 컴포넌트가 호출해도 한 번만 네트워크 요청)
  function ensureLoaded() {
    if (started) return
    started = true
    load()
  }

  return { data, error, loading, load, ensureLoaded }
}

// /api/health — 헤더 뱃지 + DB 상태 카드 공용
const health = createResource(() => api.health())
export function useHealth() {
  return health
}

// /api/stock/kr/<code> — 현재가 카드 + 최근 시세 표 공용
const krxStock = createResource(() => api.krxStock(currentCode.value))
// 종목 변경 시 공유 싱글턴을 재조회(KrxDataCard·PriceDataTable 동시 갱신)
watch(currentCode, () => krxStock.load())
export function useKrxStock() {
  return krxStock
}
