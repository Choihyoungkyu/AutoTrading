<script setup>
import { ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import KrxDataCard from './components/KrxDataCard.vue'
import DbStatusCard from './components/DbStatusCard.vue'
import PriceDataTable from './components/PriceDataTable.vue'
import PriceChart from './components/PriceChart.vue'
import FinancialAnalysis from './components/FinancialAnalysis.vue'
import ChartAnalysis from './components/ChartAnalysis.vue'
import NewsAnalysis from './components/NewsAnalysis.vue'
import RecommendationAnalysis from './components/RecommendationAnalysis.vue'
import PriceTargetCard from './components/PriceTargetCard.vue'
import AppFooter from './components/AppFooter.vue'

const tabs = [
  { key: 'recommendation', label: '🎯 종합 추천' },
  { key: 'price-target', label: '🎚️ 목표가·손절' },
  { key: 'overview', label: '📈 개요' },
  { key: 'chart', label: '📉 주가 차트' },
  { key: 'financial', label: '💰 재무 분석' },
  { key: 'technical', label: '📐 기술적 분석' },
  { key: 'news', label: '📰 뉴스' },
]
const active = ref('recommendation')
</script>

<template>
  <div class="container">
    <AppHeader />

    <nav class="tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        class="tab-btn"
        :class="{ active: active === t.key }"
        @click="active = t.key"
      >
        {{ t.label }}
      </button>
    </nav>

    <!-- keep-alive: 탭 전환 시 각 탭의 데이터/차트 상태를 보존(재요청 방지) -->
    <keep-alive>
      <RecommendationAnalysis v-if="active === 'recommendation'" key="recommendation" />
      <PriceTargetCard v-else-if="active === 'price-target'" key="price-target" />
      <div v-else-if="active === 'overview'" key="overview">
        <div class="main">
          <KrxDataCard />
          <DbStatusCard />
        </div>
        <PriceDataTable />
      </div>
      <PriceChart v-else-if="active === 'chart'" key="chart" />
      <FinancialAnalysis v-else-if="active === 'financial'" key="financial" />
      <ChartAnalysis v-else-if="active === 'technical'" key="technical" />
      <NewsAnalysis v-else-if="active === 'news'" key="news" />
    </keep-alive>

    <AppFooter />
  </div>
</template>
