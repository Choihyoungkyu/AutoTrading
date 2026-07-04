import { ref } from 'vue'

// 대시보드 전역에서 공유하는 현재 선택 종목. 검색창이 setStock으로 바꾸면
// 이 ref를 watch하는 모든 카드가 재조회한다.
// 초기값 null = 종목 미선택(홈 화면). 종목 검색 시 상세 대시보드로 전환된다.
export const currentCode = ref(null)
export const currentName = ref(null)

export function setStock(code, name) {
  currentCode.value = code
  currentName.value = name || code
}

// 홈(지수 + 검색) 화면으로 복귀
export function goHome() {
  currentCode.value = null
  currentName.value = null
}
