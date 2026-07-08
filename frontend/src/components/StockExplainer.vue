<script setup>
import { ref, watchEffect } from 'vue'
import { api, STOCK_CODE } from '../api/client'

const props = defineProps({ code: { type: String, default: STOCK_CODE } })
const data = ref(null)
const error = ref('')

watchEffect(async () => {
  data.value = null; error.value = ''
  try { data.value = await api.explain(props.code) }
  catch (e) { error.value = '상태 설명을 불러오지 못했습니다.' }
})

const sevClass = (s) => ({ warning: 'sev-warning', caution: 'sev-caution' }[s] || 'sev-info')
</script>

<template>
  <section class="explainer">
    <p class="disclaimer">⚠ {{ data?.disclaimer || '현재 상태 설명이며 투자 권유가 아닙니다.' }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="data?.risks?.length" class="group risks">
      <h3>위험 신호</h3>
      <ul>
        <li v-for="(r, i) in data.risks" :key="'r'+i" :class="sevClass(r.severity)">
          <strong>{{ r.label }}</strong> — {{ r.statement }}
        </li>
      </ul>
    </div>

    <div class="grid">
      <div class="group">
        <h3>기술적 상태</h3>
        <ul>
          <li v-for="(t, i) in data?.technical || []" :key="'t'+i" :class="sevClass(t.severity)">
            <strong>{{ t.label }}</strong> — {{ t.statement }}
          </li>
        </ul>
      </div>
      <div class="group">
        <h3>재무 상태</h3>
        <ul>
          <li v-for="(f, i) in data?.financial || []" :key="'f'+i" :class="sevClass(f.severity)">
            <strong>{{ f.label }}</strong> — {{ f.statement }}
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 모바일 우선 */
.explainer { padding: 12px; }
.disclaimer { background: #fff8e1; color: #7a5c00; padding: 10px; border-radius: 8px; font-size: 13px; }
.error { color: #c0392b; }
.group { margin-top: 14px; }
.group h3 { font-size: 16px; margin-bottom: 8px; }
.group ul { list-style: none; padding: 0; }
.group li { padding: 10px 12px; margin-bottom: 6px; border-radius: 8px; font-size: 14px; min-height: 44px; box-sizing: border-box; }
.sev-info { background: #f1f5f9; }
.sev-caution { background: #fff3cd; }
.sev-warning { background: #f8d7da; color: #842029; }
.grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
@media (min-width: 768px) {
  .explainer { padding: 20px; }
  .grid { grid-template-columns: 1fr 1fr; }
}
</style>
