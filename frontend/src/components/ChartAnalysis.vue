<script setup>
import { computed, onMounted } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'

const { data, error, loading, load } = useAsyncData(() => api.chart())
onMounted(load)

const signalColor = computed(() => {
  const s = data.value?.signal
  return s === 'buy' ? '#27ae60' : s === 'sell' ? '#e74c3c' : '#f39c12'
})
const signalKo = computed(() => {
  const s = data.value?.signal
  return s === 'buy' ? '매수' : s === 'sell' ? '매도' : '중립'
})
const rsiState = computed(() => {
  const r = data.value?.rsi
  return r < 30 ? '과매도' : r > 70 ? '과매수' : '중립'
})
const fmt = (n) => n.toLocaleString()
</script>

<template>
  <div class="card">
    <h2>📈 기술적 분석 - 차트 분석 (이슈 003)</h2>
    <div v-if="error" class="error">차트 분석 로드 실패: {{ error }}</div>
    <div v-else-if="loading || !data" class="loading">분석 중...</div>
    <div v-else style="margin-top: 15px;">
      <div style="margin-bottom: 20px;">
        <strong style="font-size: 18px;">매매 신호</strong>
        <div
          :style="{ background: signalColor }"
          style="display: inline-block; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; margin-top: 10px; font-size: 16px;"
        >
          {{ signalKo }} (신뢰도: {{ (data.confidence * 100).toFixed(0) }}%)
        </div>
        <div style="font-size: 12px; color: #7f8c8d; margin-top: 6px;">
          기준일: {{ data.as_of || '-' }}
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-box">
          <div class="metric-label">
            RSI (14주기)
            <span class="tooltip-icon" data-tooltip="상대강도지수: 0~100 범위에서 매도/매수 과열 정도를 나타냄">?</span>
          </div>
          <div class="metric-value">{{ data.rsi.toFixed(2) }}</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">{{ rsiState }}</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">
            이동평균선 20일
            <span class="tooltip-icon" data-tooltip="최근 20일간의 평균 가격. 단기 추세를 나타냄">?</span>
          </div>
          <div class="metric-value">{{ fmt(data.ma_20) }}</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            {{ data.ma_20 > data.ma_50 ? '↑ 상승추세' : '↓ 하락추세' }}
          </div>
        </div>
        <div class="metric-box">
          <div class="metric-label">
            이동평균선 50일
            <span class="tooltip-icon" data-tooltip="최근 50일간의 평균 가격. 중기 추세와 지지/저항선 역할">?</span>
          </div>
          <div class="metric-value">{{ fmt(data.ma_50) }}</div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">기준선</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">
            MACD 히스토그램
            <span class="tooltip-icon" data-tooltip="MACD 지수이동평균: 단기와 중기 추세의 교차점을 통해 신호 감지">?</span>
          </div>
          <div class="metric-value" :style="{ color: data.macd.histogram > 0 ? '#27ae60' : '#e74c3c' }">
            {{ data.macd.histogram.toFixed(2) }}
          </div>
          <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
            {{ data.macd.histogram > 0 ? '상승' : '하락' }}
          </div>
        </div>
      </div>

      <div class="comparison">
        <div class="comparison-card">
          <div class="comparison-title">
            📊 기술적 지표
            <span class="tooltip-icon" data-tooltip="MACD(Moving Average Convergence Divergence)는 단기와 중기 이동평균의 차이를 통해 추세 변화를 감지하는 지표">?</span>
          </div>
          <div style="font-size: 12px; line-height: 1.8; color: #495057;">
            <div>
              <strong>MACD Line:</strong> {{ data.macd.line.toFixed(2) }}
              <span class="tooltip-icon" data-tooltip="12일 EMA - 26일 EMA">?</span>
            </div>
            <div>
              <strong>Signal:</strong> {{ data.macd.signal.toFixed(2) }}
              <span class="tooltip-icon" data-tooltip="MACD의 9일 EMA (신호선)">?</span>
            </div>
            <div>
              <strong>Histogram:</strong> {{ data.macd.histogram.toFixed(2) }}
              <span class="tooltip-icon" data-tooltip="MACD Line - Signal의 차이 (양수=상승, 음수=하락)">?</span>
            </div>
          </div>
        </div>
        <div class="comparison-card">
          <div class="comparison-title">
            📈 볼린저밴드 (20, 2σ)
            <span class="tooltip-icon" data-tooltip="이동평균을 중심으로 표준편차 범위의 상/하단선. 가격 변동성을 나타냄">?</span>
          </div>
          <div style="font-size: 12px; line-height: 1.8; color: #495057;">
            <div>
              <strong>상단:</strong> {{ fmt(data.bollinger_band.upper) }}
              <span class="tooltip-icon" data-tooltip="저항선(과매수 신호)">?</span>
            </div>
            <div>
              <strong>중단:</strong> {{ fmt(data.bollinger_band.middle) }}
              <span class="tooltip-icon" data-tooltip="20일 이동평균선">?</span>
            </div>
            <div>
              <strong>하단:</strong> {{ fmt(data.bollinger_band.lower) }}
              <span class="tooltip-icon" data-tooltip="지지선(과매도 신호)">?</span>
            </div>
          </div>
        </div>
      </div>

      <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; font-size: 12px; color: #495057; line-height: 1.6;">
        <strong>신호 판단 규칙:</strong><br>
        • <span style="color: #27ae60;">매수:</span> RSI &lt; 30 AND 20일선 &gt; 50일선<br>
        • <span style="color: #e74c3c;">매도:</span> RSI &gt; 70 AND 20일선 &lt; 50일선<br>
        • <span style="color: #f39c12;">중립:</span> 위 조건 이외
      </div>
    </div>
  </div>
</template>
