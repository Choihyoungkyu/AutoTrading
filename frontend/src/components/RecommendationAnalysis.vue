<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAsyncData } from '../composables/useAsyncData.js'
import { api } from '../api/client.js'
import { currentCode } from '../composables/useCurrentStock.js'

const { data, error, loading, load } = useAsyncData(() => api.recommendation(currentCode.value))
onMounted(load)
watch(currentCode, load)

const grade = computed(() => data.value?.grade || 'hold')
const gradeKo = computed(() => (grade.value === 'buy' ? '매수' : grade.value === 'sell' ? '매도' : '관망'))
const gradeEn = computed(() => (grade.value === 'buy' ? 'BUY' : grade.value === 'sell' ? 'SELL' : 'HOLD'))
const heroClass = computed(() => (grade.value === 'buy' ? 'buy' : grade.value === 'sell' ? 'sell' : 'hold'))
const txClass = computed(() => (grade.value === 'buy' ? 'tx-buy' : grade.value === 'sell' ? 'tx-sell' : 'tx-hold'))

const confidence = computed(() => data.value?.confidence ?? Math.round((data.value?.score ?? 0) * 100))
const factors = computed(() => data.value?.factors || [])
const dims = computed(() => data.value?.dimensions || [])

// 점수 막대 색 (디자인 로직)
const barColor = (s) => (s >= 75 ? 'var(--buy)' : s >= 55 ? 'var(--secondary)' : 'var(--hold)')
const sigChipCls = (s) => (s === 'buy' ? 'sig-buy' : s === 'sell' ? 'sig-sell' : 'sig-hold')
const num = (v) => (v == null || isNaN(v)) ? '-' : Number(v).toLocaleString()

// 분석 기준 팝업 — 종합 추천이 어떻게 산출되는지 설명
const showInfo = ref(false)
const weights = computed(() => data.value?.weights || { financial: 0.4, chart: 0.4, news: 0.2 })
const wpct = (w) => Math.round((w ?? 0) * 100)
</script>

<template>
  <div v-if="error" class="card"><div class="error">추천 로드 실패: {{ error }}</div></div>
  <div v-else-if="loading || !data" class="card"><div class="loading">종합 분석 중...</div></div>
  <div v-else>
    <!-- Hero -->
    <div class="reco-hero" :class="heroClass">
      <button type="button" class="info-btn" @click="showInfo = true" title="분석 기준 보기">
        ⓘ 분석 기준
      </button>
      <div class="reco-eyebrow">AI 종합 시그널</div>
      <div class="reco-verdict-huge" :class="txClass">{{ gradeKo }}</div>
      <div class="reco-en" :class="txClass">{{ gradeEn }}</div>

      <div class="reco-conf">
        <div class="score-row"><span>신뢰도</span><span class="mono" :class="txClass">{{ confidence }}%</span></div>
        <div class="meter"><div class="meter-fill" :style="{ width: confidence + '%', background: 'var(--' + heroClass + ')' }"></div></div>
      </div>

      <div class="reco-pills">
        <div class="reco-pill">
          <div class="rp-label">현재가</div>
          <div class="rp-value">{{ num(data.current_price) }}</div>
        </div>
        <div class="reco-pill">
          <div class="rp-label tx-buy">목표가</div>
          <div class="rp-value tx-buy">{{ num(data.target_price) }}</div>
        </div>
        <div class="reco-pill">
          <div class="rp-label tx-sell">손절가</div>
          <div class="rp-value tx-sell">{{ num(data.stop_loss) }}</div>
        </div>
      </div>

      <div v-if="data.reasoning" class="reco-rationale">{{ data.reasoning }}</div>
    </div>

    <!-- 평가 요인별 점수 -->
    <div class="card" style="margin-top: 16px;">
      <div class="card-title" style="margin-bottom: 16px;">평가 요인별 점수</div>
      <div v-for="f in factors" :key="f.name" class="score-item">
        <div class="score-row">
          <span>{{ f.name }}</span>
          <span class="mono" style="font-weight: 700;" :style="{ color: barColor(f.score) }">{{ f.score }}</span>
        </div>
        <div class="meter"><div class="meter-fill" :style="{ width: f.score + '%', background: barColor(f.score) }"></div></div>
      </div>
    </div>

    <!-- 차원 요약 -->
    <div class="dim-grid">
      <div v-for="d in dims" :key="d.name" class="dim-card">
        <div class="dim-head">
          <span class="dim-name">{{ d.name }}</span>
          <span class="sig-chip" :class="sigChipCls(d.signal)">{{ d.tag }}</span>
        </div>
        <div class="dim-desc">{{ d.desc }}</div>
      </div>
    </div>

    <!-- 분석 기준 팝업 -->
    <Teleport to="body">
      <div v-if="showInfo" class="modal-overlay" @click.self="showInfo = false">
        <div class="modal-card" role="dialog" aria-modal="true" aria-label="분석 기준">
          <div class="modal-head">
            <span class="modal-title">종합 추천 산출 기준</span>
            <button type="button" class="modal-close" @click="showInfo = false" aria-label="닫기">✕</button>
          </div>

          <div class="modal-body">
            <section class="mb-sec">
              <h4>종합 점수 = 세 관점의 가중 평균</h4>
              <p>
                재무·차트·뉴스를 각각 0~100으로 정규화한 뒤 가중 평균합니다.
              </p>
              <ul class="mb-weights">
                <li><span class="mb-dot" style="background: var(--secondary);"></span> 재무(밸류에이션) <b>{{ wpct(weights.financial) }}%</b></li>
                <li><span class="mb-dot" style="background: var(--buy);"></span> 차트(기술적) <b>{{ wpct(weights.chart) }}%</b></li>
                <li><span class="mb-dot" style="background: var(--hold);"></span> 뉴스(심리) <b>{{ wpct(weights.news) }}%</b></li>
              </ul>
              <p class="mb-note">
                등급: 종합 65점 초과 <b class="tx-buy">매수</b> · 35~65점 <b class="tx-hold">관망</b> · 35점 미만 <b class="tx-sell">매도</b>
              </p>
            </section>

            <section class="mb-sec">
              <h4>① 재무 — 업종 내 순위비율 (KRX 밸류업 방식)</h4>
              <p>
                PER·PBR(낮을수록 우수), ROE·배당수익률(높을수록 우수)을 동일업종 종목들과 비교한
                <b>백분위 순위(0~100)</b>로 환산해 평균합니다. 절대 수치가 아닌 상대 순위라
                이상치·업종 편차에 강건합니다.
              </p>
            </section>

            <section class="mb-sec">
              <h4>② 차트 — 6개 지표 투표</h4>
              <p>
                RSI·MACD·이동평균·볼린저밴드·스토캐스틱·OBV 각각의 매수/매도 신호를 집계해
                (매수−매도)/지표수로 0~100 점수를 냅니다.
              </p>
            </section>

            <section class="mb-sec">
              <h4>③ 뉴스 — 감정 점수</h4>
              <p>
                최근 뉴스 제목의 긍·부정 감정 점수(−1~+1)를 0~1로 변환해 반영합니다.
              </p>
            </section>

            <section class="mb-sec">
              <h4>신뢰도</h4>
              <p>
                세 관점의 <b>방향 일치도</b>와 <b>신호 강도</b>를 결합해 산출합니다. 세 축이
                같은 방향(모두 매수/모두 매도)일수록, 중립에서 멀수록 높아집니다.
              </p>
            </section>

            <section class="mb-sec mb-caveat">
              <h4>⚠️ 해석 시 주의</h4>
              <p>
                이 도구는 감정을 배제한 <b>빠른 판단 보조용</b>입니다. 특히 뉴스 감정의 결합 비중은
                실증 근거가 약하며, 어떤 점수도 <b>수익을 보장하지 않습니다</b>. 투자 판단의 최종 책임은
                본인에게 있습니다.
              </p>
            </section>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.reco-hero { position: relative; }
.info-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 5px 10px;
  border: 1px solid var(--bd);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.12);
  color: inherit;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  backdrop-filter: blur(2px);
}
.info-btn:hover { background: rgba(255, 255, 255, 0.24); }

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0;
}
.modal-card {
  width: 100%;
  max-height: 88vh;
  overflow-y: auto;
  background: var(--bg, #fff);
  color: var(--tx);
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.25);
}
.modal-head {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--bg, #fff);
  border-bottom: 1px solid var(--bd);
}
.modal-title { font-size: 16px; font-weight: 700; }
.modal-close {
  border: none;
  background: transparent;
  color: var(--mut);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 8px;
}
.modal-body { padding: 16px; }
.mb-sec { margin-bottom: 18px; }
.mb-sec h4 { font-size: 14px; font-weight: 700; margin: 0 0 6px; }
.mb-sec p { font-size: 13px; line-height: 1.65; color: var(--tx); margin: 0; }
.mb-note { margin-top: 8px !important; font-size: 12px !important; color: var(--mut) !important; }
.mb-weights {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}
.mb-weights li { display: flex; align-items: center; gap: 8px; }
.mb-dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
.mb-caveat {
  background: var(--sell-bg, rgba(239, 68, 68, 0.08));
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 0;
}
.mb-caveat h4 { color: var(--sell); }

/* 태블릿·데스크탑: 중앙 다이얼로그 */
@media (min-width: 768px) {
  .modal-overlay { align-items: center; padding: 24px; }
  .modal-card { max-width: 520px; border-radius: 16px; }
  .modal-head { border-radius: 16px 16px 0 0; }
}
</style>
