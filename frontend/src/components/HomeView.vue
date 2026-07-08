<script setup>
import MarketIndices from './MarketIndices.vue'
import WatchlistPanel from './WatchlistPanel.vue'

// 홈 화면: 시장 개요(주요 지수) + 관심 종목. 검색은 상단바에서 상시 제공된다.
</script>

<template>
  <div class="home">
    <h1 class="section-title">시장 개요</h1>
    <MarketIndices />
    <WatchlistPanel />
  </div>
</template>
