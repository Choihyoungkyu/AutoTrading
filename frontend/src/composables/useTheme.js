import { ref, watch } from 'vue'

// 다크/라이트 테마 토글. data-app-theme 속성으로 CSS 토큰을 전환하고 localStorage에 보존.
// 디자인 기본값은 다크.
const STORAGE_KEY = 'app-theme'
const saved = localStorage.getItem(STORAGE_KEY)
export const theme = ref(saved === 'light' ? 'light' : 'dark')

function apply(t) {
  document.documentElement.setAttribute('data-app-theme', t)
}
apply(theme.value)

watch(theme, (t) => {
  apply(t)
  localStorage.setItem(STORAGE_KEY, t)
})

export function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}
