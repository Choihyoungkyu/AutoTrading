<script setup>
import { computed, onMounted } from 'vue'
import { useKrxStock } from '../composables/useStock.js'

const { data, error, loading, ensureLoaded } = useKrxStock()
onMounted(ensureLoaded)

// 최신순 10건
const rows = computed(() => {
  const d = data.value?.data
  return d ? d.slice().reverse().slice(0, 10) : []
})
const fmt = (n) => n.toLocaleString()
const volM = (v) => (v / 1000000).toFixed(1) + 'M'
const fmtRate = (v) => (parseFloat(v) > 0 ? '+' : '') + parseFloat(v).toFixed(2) + '%'
const changeClass = (row) => (parseFloat(row.change) > 0 ? 'value-up' : 'value-down')
</script>

<template>
  <div class="card">
    <h2>📊 최근 시세 데이터</h2>
    <table class="data-table">
      <thead>
        <tr>
          <th>날짜</th>
          <th>시가</th>
          <th>고가</th>
          <th>저가</th>
          <th>종가</th>
          <th>등락률</th>
          <th>거래량</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="error">
          <td colspan="7" class="error">데이터 로드 실패</td>
        </tr>
        <tr v-else-if="loading || !rows.length">
          <td colspan="7" class="loading">데이터 로드 중...</td>
        </tr>
        <tr v-for="row in rows" v-else :key="row.date">
          <td>{{ row.date }}</td>
          <td>{{ fmt(row.open) }}</td>
          <td>{{ fmt(row.high) }}</td>
          <td>{{ fmt(row.low) }}</td>
          <td><strong>{{ fmt(row.close) }}</strong></td>
          <td :class="changeClass(row)">{{ fmtRate(row.change) }}</td>
          <td>{{ volM(row.volume) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
