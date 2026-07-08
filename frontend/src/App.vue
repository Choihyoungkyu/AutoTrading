<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import AppHeader from './components/AppHeader.vue'
import HomeView from './components/HomeView.vue'
import VolumeRanking from './components/VolumeRanking.vue'
import KrxDataCard from './components/KrxDataCard.vue'
import AiSignalCard from './components/AiSignalCard.vue'
import PriceDataTable from './components/PriceDataTable.vue'
import PriceChart from './components/PriceChart.vue'
import FinancialAnalysis from './components/FinancialAnalysis.vue'
import ChartAnalysis from './components/ChartAnalysis.vue'
import NewsAnalysis from './components/NewsAnalysis.vue'
import RecommendationAnalysis from './components/RecommendationAnalysis.vue'
import PriceTargetCard from './components/PriceTargetCard.vue'
import AppFooter from './components/AppFooter.vue'
import StockSearch from './components/StockSearch.vue'
import { currentCode, currentName, goHome } from './composables/useCurrentStock.js'
import { theme, toggleTheme } from './composables/useTheme.js'

const tabs = [
  { key: 'overview', label: '📈 개요' },
  { key: 'chart', label: '📉 주가 차트' },
  { key: 'financial', label: '💰 재무 분석' },
  { key: 'technical', label: '📐 기술적 분석' },
  { key: 'news', label: '📰 뉴스' },
  { key: 'price-target', label: '🎚️ 목표가·손절' },
  { key: 'recommendation', label: '🎯 종합 추천' },
]
const active = ref('overview')

// 종목을 검색/변경하면 항상 개요 탭부터 보여준다.
watch(currentCode, () => { active.value = 'overview' })

// 홈 영역에서 보여줄 화면: 'home'(시장개요) | 'ranking'(거래량 상위)
const homeSection = ref('home')
// 거래량 상위 시장: 'KOSPI' | 'KOSDAQ'
const rankingMarket = ref('KOSPI')

// 모바일 사이드바(드로어) 열림 상태
const sidebarOpen = ref(false)
function selectTab(key) { active.value = key; sidebarOpen.value = false }
function navHome() { goHome(); homeSection.value = 'home'; sidebarOpen.value = false }
function navRanking(market = 'KOSPI') {
  goHome(); homeSection.value = 'ranking'; rankingMarket.value = market; sidebarOpen.value = false
}

// 실시간 데이터 새로고침: content-inner를 리마운트해 현재 화면의 모든 API를 재요청한다.
// (탭·선택 종목 등 상위 상태는 유지되고, 자식 컴포넌트만 다시 로드)
const refreshKey = ref(0)
const refreshing = ref(false)
let refreshTimer = null
function refreshData() {
  refreshKey.value++
  sidebarOpen.value = false
  refreshing.value = true
  clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => { refreshing.value = false }, 700)
}

// 상단바 실시간 시계 (HH:MM)
const clock = ref('')
function tick() {
  const d = new Date()
  clock.value = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
}
tick()
const timer = setInterval(tick, 15000)
onBeforeUnmount(() => { clearInterval(timer); clearTimeout(refreshTimer) })
</script>

<template>
  <div class="app-shell">
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>

    <!-- ===== 사이드바 ===== -->
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-logo">
        <div class="logo-mark">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff"
               stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 17l5-6 4 4 8-9"></path>
            <path d="M17 6h4v4"></path>
          </svg>
        </div>
        <div class="logo-text">Stockscope</div>
      </div>

      <div class="sidebar-refresh">
        <button class="refresh-btn" :class="{ spinning: refreshing }" :disabled="refreshing"
                @click="refreshData" title="실시간 주가 데이터 새로고침">
          <span class="refresh-icon">⟳</span>
          <span>{{ refreshing ? '갱신 중…' : '새로고침' }}</span>
        </button>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-label">MENU</div>
        <button class="nav-btn" :class="{ active: !currentCode && homeSection === 'home' }" @click="navHome">
          <span>🏠 홈</span>
        </button>
        <button class="nav-btn" :class="{ active: !currentCode && homeSection === 'ranking' && rankingMarket === 'KOSPI' }" @click="navRanking('KOSPI')">
          <span>🔥 거래량 상위 (KOSPI)</span>
        </button>
        <button class="nav-btn" :class="{ active: !currentCode && homeSection === 'ranking' && rankingMarket === 'KOSDAQ' }" @click="navRanking('KOSDAQ')">
          <span>🔥 거래량 상위 (KOSDAQ)</span>
        </button>

        <template v-if="currentCode">
          <div class="nav-label section">종목 분석 · {{ currentName }}</div>
          <button
            v-for="t in tabs"
            :key="t.key"
            class="nav-btn"
            :class="{ active: active === t.key }"
            @click="selectTab(t.key)"
          >
            <span>{{ t.label }}</span>
            <span v-if="t.key === 'recommendation'" class="nav-badge">AI</span>
          </button>
        </template>
      </nav>

      <div class="theme-toggle-wrap">
        <button class="theme-toggle" @click="toggleTheme">
          <span>{{ theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환' }}</span>
          <span class="short">{{ theme === 'dark' ? 'DARK' : 'LIGHT' }}</span>
        </button>
      </div>
    </aside>

    <!-- ===== 메인 ===== -->
    <div class="main-area">
      <header class="topbar">
        <button class="hamburger" aria-label="메뉴 열기" @click="sidebarOpen = true">☰</button>
        <StockSearch placeholder="종목명 또는 종목코드 검색 (예: SK하이닉스, 000660)" />
        <div class="market-ticker">
          <span>{{ clock }} KST</span>
        </div>
      </header>

      <div class="content-scroll">
        <div class="content-inner" :key="refreshKey">
          <template v-if="!currentCode">
            <HomeView v-if="homeSection === 'home'" />
            <VolumeRanking v-else :market="rankingMarket" />
          </template>

          <template v-else>
            <AppHeader />

            <!-- 모바일 전용 탭바(데스크탑은 사이드바 사용) -->
            <nav class="tabs content-tabs">
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
                <div class="split">
                  <KrxDataCard />
                  <AiSignalCard @goto="active = $event" />
                </div>
                <PriceDataTable />
              </div>
              <PriceChart v-else-if="active === 'chart'" key="chart" />
              <FinancialAnalysis v-else-if="active === 'financial'" key="financial" />
              <ChartAnalysis v-else-if="active === 'technical'" key="technical" />
              <NewsAnalysis v-else-if="active === 'news'" key="news" />
            </keep-alive>

            <AppFooter />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
