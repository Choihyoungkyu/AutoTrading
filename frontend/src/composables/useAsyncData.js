import { ref } from 'vue'

// 컴포넌트별 1회성 API 호출의 로딩/에러/데이터 상태 헬퍼.
// (공유가 필요한 엔드포인트는 useStock.js의 싱글턴을 사용)
export function useAsyncData(loader) {
  const data = ref(null)
  const error = ref(null)
  const loading = ref(true)

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

  return { data, error, loading, load }
}
