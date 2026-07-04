import { ref } from 'vue'

// 대시보드 전역에서 공유하는 현재 선택 종목. 검색창이 setStock으로 바꾸면
// 이 ref를 watch하는 모든 카드가 재조회한다.
export const currentCode = ref('005930')
export const currentName = ref('삼성전자')

export function setStock(code, name) {
  currentCode.value = code
  currentName.value = name || code
}
