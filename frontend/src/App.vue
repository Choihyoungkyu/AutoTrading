<script setup>
import AppHeader from './components/AppHeader.vue'
import KrxDataCard from './components/KrxDataCard.vue'
import DbStatusCard from './components/DbStatusCard.vue'
import PriceDataTable from './components/PriceDataTable.vue'
import PriceChart from './components/PriceChart.vue'
import FinancialAnalysis from './components/FinancialAnalysis.vue'
import ChartAnalysis from './components/ChartAnalysis.vue'
import AppFooter from './components/AppFooter.vue'
</script>

<template>
  <div class="container">
    <AppHeader />

    <div class="main">
      <KrxDataCard />
      <DbStatusCard />
    </div>

    <PriceDataTable />
    <PriceChart />
    <FinancialAnalysis />
    <ChartAnalysis />
    <AppFooter />
  </div>
</template>
