<script setup>
import { computed, onMounted } from 'vue'
import { useHealth } from '../composables/useStock.js'
import { currentCode, currentName } from '../composables/useCurrentStock.js'
import { isFavorite, toggleFavorite } from '../composables/useWatchlist.js'

const faved = computed(() => isFavorite(currentCode.value))

const { data, error, ensureLoaded } = useHealth()
onMounted(ensureLoaded)

const dbText = computed(() => {
  if (error.value) return '✗ 오류'
  if (!data.value) return '연결 중...'
  return data.value.status === 'ok' ? '✓ 정상 연결' : '✗ 연결 실패'
})
const dbClass = computed(() => {
  if (!data.value || error.value) return error.value ? 'status-error' : ''
  return data.value.status === 'ok' ? 'status-ok' : 'status-error'
})
</script>

<template>
  <div class="stock-header">
    <div class="stock-title-row">
      <span class="stock-name">{{ currentName }}</span>
      <span class="stock-code">{{ currentCode }}</span>
      <button
        class="fav-btn"
        :class="{ on: faved }"
        :title="faved ? '관심 종목 해제' : '관심 종목 추가'"
        @click="toggleFavorite(currentCode, currentName)"
      >{{ faved ? '❤️' : '🤍' }}</button>
    </div>
  </div>
</template>
