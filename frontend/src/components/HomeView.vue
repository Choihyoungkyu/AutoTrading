<script setup>
import MarketIndices from './MarketIndices.vue'
import WatchlistPanel from './WatchlistPanel.vue'
import StockSearch from './StockSearch.vue'

// 홈 화면: 주요 지수 + 종목 검색만. 종목을 검색하면 상세 대시보드로 전환된다.
</script>

<template>
  <div class="home">
    <div class="home-hero">
      <h1>📈 주식 분석 시스템</h1>
      <p>종목을 검색해 재무·차트·뉴스·추천을 한 번에 확인하세요.</p>
      <StockSearch />
    </div>
    <MarketIndices />
    <WatchlistPanel />
  </div>
</template>
