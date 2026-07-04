<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'
import { api } from '../api/client.js'
import { currentCode, currentName } from '../composables/useCurrentStock.js'

const PERIODS = [
  { key: '1d', label: '일' },
  { key: '1w', label: '주' },
  { key: '1m', label: '달' },
  { key: '1y', label: '년' },
]

const INDICATORS = [
  { key: 'ma5', label: 'MA5', color: '#e74c3c', tooltip: '최근 5일 평균가격. 가장 빠른 단기 추세 변화를 나타냄' },
  { key: 'ma20', label: 'MA20', color: '#f39c12', tooltip: '최근 20일 평균가격. 단기 추세와 매매신호를 나타냄' },
  { key: 'ma60', label: 'MA60', color: '#2980b9', tooltip: '최근 60일 평균가격. 중기 추세의 흐름을 나타냄' },
  { key: 'bb', label: '볼린저밴드', color: '#9b59b6', tooltip: '이동평균을 중심으로 표준편차 범위의 밴드. 가격 변동성과 과매수/과매도를 나타냄' },
]

const period = ref('1m')
const active = reactive({ ma5: false, ma20: true, ma60: false, bb: false })
const asof = ref('')
const errorMsg = ref('')

const canvas = ref(null)
let chartInstance = null
let chartData = null

function indStyle(ind) {
  return active[ind.key]
    ? { borderColor: ind.color, background: ind.color, color: 'white' }
    : { borderColor: ind.color, background: 'white', color: ind.color }
}

function toggleIndicator(key) {
  active[key] = !active[key]
  if (chartData) renderChart()
}

function buildDatasets() {
  const rows = chartData.data
  const datasets = [{
    label: '종가',
    data: rows.map((d) => d.close),
    borderColor: '#2c3e50',
    backgroundColor: (() => {
      const ctx = canvas.value.getContext('2d')
      const gradient = ctx.createLinearGradient(0, 0, 0, 320)
      gradient.addColorStop(0, 'rgba(44,62,80,0.25)')
      gradient.addColorStop(1, 'rgba(44,62,80,0)')
      return gradient
    })(),
    borderWidth: 2,
    pointRadius: rows.length > 60 ? 0 : 2,
    fill: true,
    tension: 0.1,
  }]

  const lineMA = (key, label, color) => ({
    label,
    data: rows.map((d) => d[key]),
    borderColor: color,
    borderWidth: 1.5,
    pointRadius: 0,
    fill: false,
    tension: 0.1,
  })

  if (active.ma5) datasets.push(lineMA('ma5', 'MA5', '#e74c3c'))
  if (active.ma20) datasets.push(lineMA('ma20', 'MA20', '#f39c12'))
  if (active.ma60) datasets.push(lineMA('ma60', 'MA60', '#2980b9'))
  if (active.bb) {
    datasets.push({
      label: 'BB Upper',
      data: rows.map((d) => d.bb_upper),
      borderColor: '#9b59b6',
      borderWidth: 1.5,
      borderDash: [4, 4],
      pointRadius: 0,
      fill: false,
      tension: 0.1,
    })
    datasets.push({
      label: 'BB Lower',
      data: rows.map((d) => d.bb_lower),
      borderColor: '#9b59b6',
      borderWidth: 1.5,
      borderDash: [4, 4],
      pointRadius: 0,
      fill: '-1',
      backgroundColor: 'rgba(155,89,182,0.1)',
      tension: 0.1,
    })
  }
  return datasets
}

function renderChart() {
  const rows = chartData.data
  const labels = rows.map((d) => d.date)
  asof.value = rows.length ? '기준일: ' + rows[rows.length - 1].date : ''

  if (chartInstance) chartInstance.destroy()
  chartInstance = new Chart(canvas.value.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: buildDatasets() },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) =>
              ctx.dataset.label + ': ₩' + (ctx.parsed.y ? ctx.parsed.y.toLocaleString() : 'N/A'),
          },
        },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, maxRotation: 0, font: { size: 11 } },
          grid: { display: false },
        },
        y: {
          ticks: { callback: (v) => '₩' + v.toLocaleString(), font: { size: 11 } },
        },
      },
    },
  })
}

async function loadPriceChart(p) {
  period.value = p
  errorMsg.value = ''
  try {
    const data = await api.priceHistory(p, currentCode.value)
    if (data.error) {
      errorMsg.value = data.error
      return
    }
    chartData = data
    renderChart()
  } catch (e) {
    errorMsg.value = '차트 로드 실패: ' + e.message
  }
}

onMounted(() => loadPriceChart('1m'))
// 종목 변경 시 현재 기간으로 재조회
watch(currentCode, () => loadPriceChart(period.value))
onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})
</script>

<template>
  <div class="card">
    <h2>📉 주가 차트 ({{ currentName }} {{ currentCode }})</h2>
    <div class="period-buttons">
      <button
        v-for="p in PERIODS"
        :key="p.key"
        class="period-btn"
        :class="{ active: period === p.key }"
        @click="loadPriceChart(p.key)"
      >
        {{ p.label }}
      </button>
    </div>
    <div class="indicator-filters">
      <button
        v-for="ind in INDICATORS"
        :key="ind.key"
        class="ind-btn"
        :class="{ active: active[ind.key] }"
        :style="indStyle(ind)"
        :data-tooltip="ind.tooltip"
        @click="toggleIndicator(ind.key)"
      >
        {{ ind.label }}
      </button>
    </div>
    <div style="font-size:12px;color:#7f8c8d;margin-top:8px;">{{ asof }}</div>
    <div class="price-chart-wrap">
      <canvas ref="canvas"></canvas>
    </div>
    <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
  </div>
</template>
