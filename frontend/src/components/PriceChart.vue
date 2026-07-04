<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import Chart from 'chart.js/auto'
import zoomPlugin from 'chartjs-plugin-zoom'
import Hammer from 'hammerjs'
import { api } from '../api/client.js'
import { currentCode, currentName } from '../composables/useCurrentStock.js'

// 터치 핀치 줌을 위해 Hammer를 전역에 노출(chartjs-plugin-zoom이 참조)
if (typeof window !== 'undefined' && !window.Hammer) window.Hammer = Hammer
Chart.register(zoomPlugin)

const INTERVALS = [
  { key: 'day', label: '일별' },
  { key: 'week', label: '주간' },
  { key: 'month', label: '월별' },
  { key: 'year', label: '연도별' },
]

const INDICATORS = [
  { key: 'ma5', label: 'MA5', color: '#e74c3c', tooltip: '최근 5일 평균가격. 가장 빠른 단기 추세 변화를 나타냄' },
  { key: 'ma20', label: 'MA20', color: '#f39c12', tooltip: '최근 20일 평균가격. 단기 추세와 매매신호를 나타냄' },
  { key: 'ma60', label: 'MA60', color: '#2980b9', tooltip: '최근 60일 평균가격. 중기 추세의 흐름을 나타냄' },
  { key: 'bb', label: '볼린저밴드', color: '#9b59b6', tooltip: '이동평균을 중심으로 표준편차 범위의 밴드. 가격 변동성과 과매수/과매도를 나타냄' },
]

// 초기 화면에 보여줄 최근 거래일 수(축소하면 과거 전체까지 표시)
const INITIAL_WINDOW = 120

const interval = ref('day')
const active = reactive({ ma5: false, ma20: true, ma60: false, bb: false })
const asof = ref('')
const latestRate = ref(null)   // 최신 봉 등락률(%)
const errorMsg = ref('')

const canvas = ref(null)
let chartInstance = null
let chartData = null
let savedWindow = null   // 지표 토글 시 확대/이동 상태 보존용 {min, max}

function indStyle(ind) {
  return active[ind.key]
    ? { borderColor: ind.color, background: ind.color, color: 'white' }
    : { borderColor: ind.color, background: 'white', color: ind.color }
}

function toggleIndicator(key) {
  active[key] = !active[key]
  if (!chartData) return
  // 지표만 켜고 끌 때는 현재 확대/이동 상태를 유지한다.
  if (chartInstance) savedWindow = { min: chartInstance.scales.x.min, max: chartInstance.scales.x.max }
  renderChart()
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
    pointRadius: 0,
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

function applyWindow(len) {
  // 지표 토글로 재생성된 경우 직전 확대/이동 상태를 복원, 아니면 최근 구간을 기본 표시
  const range = savedWindow || { min: Math.max(0, len - INITIAL_WINDOW), max: len - 1 }
  chartInstance.zoomScale('x', range, 'none')
}

function renderChart() {
  const rows = chartData.data
  const labels = rows.map((d) => d.date)
  asof.value = rows.length ? '기준일: ' + rows[rows.length - 1].date + ` · 총 ${rows.length}거래일` : ''
  const n = rows.length
  latestRate.value =
    n >= 2 && rows[n - 2].close ? ((rows[n - 1].close - rows[n - 2].close) / rows[n - 2].close) * 100 : null

  // savedWindow(지표 토글 시 설정)가 있으면 그 범위를, 없으면 최근 구간을 표시
  if (chartInstance) chartInstance.destroy()
  chartInstance = new Chart(canvas.value.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: buildDatasets() },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) =>
              ctx.dataset.label + ': ₩' + (ctx.parsed.y ? ctx.parsed.y.toLocaleString() : 'N/A'),
            // 시가·고가·저가 + 등락률(이전 봉 대비, 간격 무관하게 계산). 종가는 라벨 줄에 표시됨.
            afterBody: (items) => {
              const i = items[0]?.dataIndex
              if (i == null) return ''
              const r = rows[i]
              if (!r) return ''
              const won = (v) => '₩' + Number(v).toLocaleString()
              const lines = [
                '시가: ' + won(r.open),
                '고가: ' + won(r.high),
                '저가: ' + won(r.low),
              ]
              const prev = rows[i - 1]?.close
              if (i > 0 && prev && r.close) {
                const rate = ((r.close - prev) / prev) * 100
                lines.push(`등락률: ${rate > 0 ? '+' : ''}${rate.toFixed(2)}%`)
              } else {
                lines.push('등락률: -')
              }
              return lines
            },
          },
        },
        zoom: {
          pan: { enabled: true, mode: 'x' },
          zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: 'x',
          },
          limits: { x: { minRange: 5 } },
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
  applyWindow(labels.length)
}

function selectInterval(key) {
  if (interval.value === key) return
  interval.value = key
  loadPriceChart()
}

async function loadPriceChart() {
  errorMsg.value = ''
  try {
    const data = await api.priceHistory('all', currentCode.value, interval.value)
    if (data.error) {
      errorMsg.value = data.error
      return
    }
    chartData = data
    savedWindow = null   // 새 종목·새 간격은 최근 구간부터 표시
    renderChart()
  } catch (e) {
    errorMsg.value = '차트 로드 실패: ' + e.message
  }
}

onMounted(loadPriceChart)
// 종목 변경 시 재조회
watch(currentCode, loadPriceChart)
onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})
</script>

<template>
  <div class="card">
    <h2>📉 주가 차트 ({{ currentName }} {{ currentCode }})</h2>
    <div class="period-buttons">
      <button
        v-for="iv in INTERVALS"
        :key="iv.key"
        class="period-btn"
        :class="{ active: interval === iv.key }"
        @click="selectInterval(iv.key)"
      >
        {{ iv.label }}
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
    <div class="chart-hint">💡 마우스 휠(또는 핀치)로 확대·축소, 드래그로 기간 이동</div>
    <div style="font-size:12px;color:#7f8c8d;margin-top:4px;">
      {{ asof }}
      <span v-if="latestRate != null" :class="latestRate > 0 ? 'value-up' : 'value-down'" style="font-weight:600;">
        · 등락률 {{ latestRate > 0 ? '+' : '' }}{{ latestRate.toFixed(2) }}%
      </span>
    </div>
    <div class="price-chart-wrap">
      <canvas ref="canvas"></canvas>
    </div>
    <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
  </div>
</template>
