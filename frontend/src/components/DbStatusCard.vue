<script setup>
import { onMounted } from 'vue'
import { useHealth } from '../composables/useStock.js'

const { data, error, ensureLoaded } = useHealth()
onMounted(ensureLoaded)
</script>

<template>
  <div class="card">
    <h2>💾 데이터베이스 상태</h2>
    <div v-if="error" class="error">✗ 오류: {{ error }}</div>
    <div v-else-if="!data" class="loading">확인 중...</div>
    <div v-else-if="data.status === 'ok'">
      <span class="status-ok">✓ SQLite 데이터베이스 연결됨</span>
      <p style="margin-top: 10px; color: var(--mut);">경로: data/stock_data.db</p>
    </div>
    <div v-else>
      <span class="status-error">✗ 데이터베이스 연결 실패</span>
    </div>
  </div>
</template>
