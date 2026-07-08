# 정직한 종목 상태 설명 도구 — 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 한 종목의 현재 기술적·재무 상태를 투명한 규칙으로 서술하고 위험 신호를 표시하는 도구(예측 없음)를 앱에 추가한다.

**Architecture:** 순수 규칙 함수 `stock_explainer.explain()`가 핵심. Flask 라우트가 기존 `chart_analyzer`·`financial_analyzer`의 현재값을 모아 `explain()`에 넘기고 JSON 반환. Vue 새 패널이 표시. 예측 모델·SHAP·매수등급은 노출하지 않는다.

**Tech Stack:** Python 3.11 / Flask(Blueprint) / pytest / Vue 3(`<script setup>`) / Vite.

## Global Constraints

- 예측·확률·매수/매도 등급 없음. 모든 응답에 고지 `현재 상태 설명이며 투자 권유가 아닙니다.` 포함.
- `chart_analyzer`의 `signal`/`confidence`(예측 태그)를 **사용하지 않는다** — 숫자 지표만 사용.
- 기존 라우트·규칙엔진(`recommendation_engine.py`)·기존 컴포넌트 **미변경**(신규만 추가). ADR 0008 병존.
- 임계값 단일 출처: Task 1의 상수. 스펙 `docs/superpowers/specs/2026-07-08-stock-explainer-design.md`와 일치.
- 반응형 표준(CLAUDE.md): 모바일 1열→데스크탑 다열, 터치 타깃 ≥44px.
- 테스트 실행: `./venv/bin/python -m pytest -q <file>`.

---

### Task 1: stock_explainer 순수 함수

**Files:**
- Create: `src/analyzers/stock_explainer.py`
- Test: `tests/test_stock_explainer.py`

**Interfaces:**
- Consumes: 없음(순수 함수, dict 입력).
- Produces: `explain(indicators: dict, financials: dict, liquidity: dict | None = None) -> dict`
  반환 `{"technical": list, "financial": list, "risks": list, "disclaimer": str}`.
  각 항목은 `{"label": str, "statement": str, "severity": "info"|"caution"|"warning"}`.
  모듈 상수: `DISCLAIMER`, `RSI_OVERSOLD=30`, `RSI_OVERBOUGHT=70`, `DEBT_RATIO_HIGH=200.0`,
  `PBR_UNDERVALUED=1.0`, `LOW_LIQUIDITY_VALUE=1_000_000_000`.

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_stock_explainer.py`

```python
from src.analyzers.stock_explainer import explain, DISCLAIMER


def test_rsi_oversold_is_info():
    r = explain({"rsi": 20}, {})
    rsi = [x for x in r["technical"] if x["label"] == "RSI"][0]
    assert "과매도" in rsi["statement"] and rsi["severity"] == "info"


def test_rsi_overbought_is_caution_and_in_risks():
    r = explain({"rsi": 80}, {})
    rsi = [x for x in r["technical"] if x["label"] == "RSI"][0]
    assert "과매수" in rsi["statement"] and rsi["severity"] == "caution"
    assert any(x["label"] == "RSI" for x in r["risks"])


def test_macd_and_ma_arrangement():
    r = explain({"macd_line": 5, "macd_signal": 3, "ma_20": 100, "ma_50": 90}, {})
    labels = {x["label"]: x["statement"] for x in r["technical"]}
    assert "상승 모멘텀" in labels["MACD"]
    assert "정배열" in labels["이동평균"]


def test_high_debt_and_negative_roe_are_warnings():
    r = explain({}, {"debt_ratio": 250, "roe": -5})
    sev = {x["label"]: x["severity"] for x in r["financial"]}
    assert sev["부채비율"] == "warning" and sev["ROE"] == "warning"
    assert len(r["risks"]) == 2


def test_pbr_undervalued_boundary():
    assert any("저평가" in x["statement"] for x in explain({}, {"pbr": 0.7})["financial"])
    assert not any(x["label"] == "PBR" for x in explain({}, {"pbr": 1.0})["financial"])


def test_low_liquidity_warning_optional():
    r = explain({}, {}, liquidity={"trade_value": 500_000_000})
    assert any(x["label"] == "유동성" and x["severity"] == "warning" for x in r["technical"])


def test_missing_fields_are_skipped_and_disclaimer_present():
    r = explain({}, {})
    assert r["technical"] == [] and r["financial"] == []
    assert r["disclaimer"] == DISCLAIMER
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest -q tests/test_stock_explainer.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.analyzers.stock_explainer'`

- [ ] **Step 3: 최소 구현** — `src/analyzers/stock_explainer.py`

```python
"""정직한 종목 상태 설명 + 리스크 표시. 예측 없음 — 현재 상태 서술과 위험 표시만."""

DISCLAIMER = "현재 상태 설명이며 투자 권유가 아닙니다."

# 임계값 단일 출처 (스펙 문서와 일치). 판단 개입 수치이므로 보수적으로.
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
DEBT_RATIO_HIGH = 200.0
PBR_UNDERVALUED = 1.0
LOW_LIQUIDITY_VALUE = 1_000_000_000  # 일 거래대금 10억원 미만 = 저유동성


def _num(v):
    """숫자로 해석 가능하면 float, 아니면 None."""
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def explain(indicators, financials, liquidity=None):
    """현재 지표·재무를 투명 규칙으로 서술/경고한다. 필드 결측 규칙은 건너뛴다."""
    technical, financial = [], []

    rsi = _num(indicators.get("rsi"))
    if rsi is not None:
        if rsi < RSI_OVERSOLD:
            technical.append({"label": "RSI", "statement": f"RSI {rsi:.0f} — 단기 과매도 구간", "severity": "info"})
        elif rsi > RSI_OVERBOUGHT:
            technical.append({"label": "RSI", "statement": f"RSI {rsi:.0f} — 단기 과매수, 과열 주의", "severity": "caution"})
        else:
            technical.append({"label": "RSI", "statement": f"RSI {rsi:.0f} — 중립 구간", "severity": "info"})

    ml, ms = _num(indicators.get("macd_line")), _num(indicators.get("macd_signal"))
    if ml is not None and ms is not None:
        up = ml > ms
        technical.append({"label": "MACD",
                          "statement": "MACD가 시그널 위 — 상승 모멘텀" if up else "MACD가 시그널 아래 — 하락 모멘텀",
                          "severity": "info"})

    m20, m50 = _num(indicators.get("ma_20")), _num(indicators.get("ma_50"))
    if m20 is not None and m50 is not None:
        up = m20 > m50
        technical.append({"label": "이동평균",
                          "statement": "단기(20)>중기(50) — 상승 배열(정배열)" if up else "단기(20)<중기(50) — 하락 배열(역배열)",
                          "severity": "info"})

    bb = indicators.get("bb_state")
    if bb == "상단":
        technical.append({"label": "볼린저밴드", "statement": "밴드 상단 — 단기 과열 주의", "severity": "caution"})
    elif bb == "하단":
        technical.append({"label": "볼린저밴드", "statement": "밴드 하단 이탈", "severity": "caution"})

    if liquidity is not None:
        tv = _num(liquidity.get("trade_value"))
        if tv is not None and tv < LOW_LIQUIDITY_VALUE:
            technical.append({"label": "유동성", "statement": "저유동성 — 슬리피지·상폐 위험 주의", "severity": "warning"})

    pbr = _num(financials.get("pbr"))
    if pbr is not None and 0 < pbr < PBR_UNDERVALUED:
        financial.append({"label": "PBR", "statement": f"PBR {pbr:.2f} — 자산 대비 저평가 구간", "severity": "info"})

    per = _num(financials.get("per"))
    if per is not None:
        if per > 0:
            financial.append({"label": "PER", "statement": f"PER {per:.1f}", "severity": "info"})
        else:
            financial.append({"label": "PER", "statement": "PER 산출 불가(적자 등)", "severity": "caution"})

    debt = _num(financials.get("debt_ratio"))
    if debt is not None and debt > DEBT_RATIO_HIGH:
        financial.append({"label": "부채비율", "statement": f"부채비율 {debt:.0f}% — 재무 부담 높음", "severity": "warning"})

    roe = _num(financials.get("roe"))
    if roe is not None and roe < 0:
        financial.append({"label": "ROE", "statement": f"ROE {roe:.1f}% — 자본 수익성 마이너스", "severity": "warning"})

    div = _num(financials.get("dividend_yield"))
    if div is not None and div > 0:
        financial.append({"label": "배당", "statement": f"배당수익률 {div:.2f}%", "severity": "info"})

    risks = [x for x in technical + financial if x["severity"] in ("caution", "warning")]
    return {"technical": technical, "financial": financial, "risks": risks, "disclaimer": DISCLAIMER}
```

- [ ] **Step 4: 통과 확인**

Run: `./venv/bin/python -m pytest -q tests/test_stock_explainer.py`
Expected: PASS (7 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/analyzers/stock_explainer.py tests/test_stock_explainer.py
git commit -m "feat: stock_explainer 순수 규칙 함수(상태 서술+리스크, 예측 없음)"
```

---

### Task 2: Flask 엔드포인트 `/analyze/<code>/explain`

**Files:**
- Modify: `src/api/routes.py` (import 추가 + 라우트 추가; 기존 라우트 미변경)
- Test: `tests/test_explainer_route.py`

**Interfaces:**
- Consumes: `explain()` (Task 1); 모듈 전역 `chart_analyzer`, `financial_analyzer` (routes.py에 기존 존재).
- Produces: `GET /analyze/<code>/explain` → `explain()` 결과 + `{"code", "as_of"}`. 데이터 없으면 404.
  라우트는 `chart_analyzer.analyze()`의 숫자만 매핑(rsi, macd.line/signal, ma_20, ma_50);
  `signal`/`confidence`는 넘기지 않는다. bb_state·liquidity는 이번 범위에서 매핑하지 않음(explain에서 선택·스킵).

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_explainer_route.py`

```python
from unittest.mock import patch, MagicMock


def _client():
    from main import create_app
    return create_app().test_client()


def test_explain_route_returns_statements_and_disclaimer():
    chart = {"rsi": 80, "macd": {"line": 1, "signal": 2}, "ma_20": 90, "ma_50": 100,
             "signal": "sell", "confidence": 0.9, "as_of": "20260708"}
    fin = {"pbr": 0.7, "per": 10, "debt_ratio": 250, "roe": -3, "dividend_yield": 2.0}
    with patch("src.api.routes.chart_analyzer") as ca, \
         patch("src.api.routes.financial_analyzer") as fa:
        ca.analyze.return_value = chart
        fa.get_financial_metrics.return_value = fin
        res = _client().get("/analyze/005930/explain")
    assert res.status_code == 200
    body = res.get_json()
    assert body["disclaimer"] == "현재 상태 설명이며 투자 권유가 아닙니다."
    assert body["code"] == "005930"
    # 예측 태그(sell/confidence)는 응답에 없어야 한다
    assert "signal" not in body and "confidence" not in body
    assert any(x["severity"] == "warning" for x in body["risks"])


def test_explain_route_404_when_no_chart_data():
    with patch("src.api.routes.chart_analyzer") as ca:
        ca.analyze.return_value = None
        res = _client().get("/analyze/000000/explain")
    assert res.status_code == 404
```

- [ ] **Step 2: 실패 확인**

Run: `./venv/bin/python -m pytest -q tests/test_explainer_route.py`
Expected: FAIL — 404가 아니라 라우트 없음(404 for unknown route 아닌, jsonify 구조 불일치) 또는 200 미달. 최소 `test_explain_route_returns_statements_and_disclaimer`가 실패.

- [ ] **Step 3: import 추가** — `src/api/routes.py` 상단 import 블록에 추가

```python
from src.analyzers.stock_explainer import explain
```

- [ ] **Step 4: 라우트 추가** — `src/api/routes.py`의 `analyze_chart` 라우트 바로 아래에 삽입

```python
@api_bp.route("/analyze/<code>/explain")
def analyze_explain(code):
    # 현재 상태 서술 + 리스크. 예측 아님(chart의 signal/confidence는 쓰지 않음).
    try:
        chart = chart_analyzer.analyze(code)
        if not chart:
            return jsonify({"error": "No data found for code: " + code}), 404
        fin = financial_analyzer.get_financial_metrics(code) or {}
        macd = chart.get("macd") or {}
        indicators = {
            "rsi": chart.get("rsi"),
            "macd_line": macd.get("line"),
            "macd_signal": macd.get("signal"),
            "ma_20": chart.get("ma_20"),
            "ma_50": chart.get("ma_50"),
        }
        result = explain(indicators, fin)
        result["code"] = code
        result["as_of"] = chart.get("as_of")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

- [ ] **Step 5: 통과 확인 + 회귀**

Run: `./venv/bin/python -m pytest -q tests/test_explainer_route.py tests/test_stock_explainer.py`
Expected: PASS (전부)

- [ ] **Step 6: 커밋**

```bash
git add src/api/routes.py tests/test_explainer_route.py
git commit -m "feat: /analyze/<code>/explain 엔드포인트(상태 설명, 예측 태그 제외)"
```

---

### Task 3: 프론트 연동 (client + 패널 + 탭)

**Files:**
- Modify: `frontend/src/api/client.js` (api 객체에 `explain` 추가)
- Create: `frontend/src/components/StockExplainer.vue`
- Modify: `frontend/src/App.vue` (import + tabs 항목 + 컴포넌트 분기 추가)

**Interfaces:**
- Consumes: `GET /analyze/<code>/explain` (Task 2).
- Produces: 사용자용 "상태 설명" 탭.

- [ ] **Step 1: client.js에 API 추가** — `api` 객체 안, `chart:` 줄 아래에 추가

```javascript
  explain: (code = STOCK_CODE) => getJson(`/analyze/${code}/explain`),
```

- [ ] **Step 2: StockExplainer.vue 생성** — `frontend/src/components/StockExplainer.vue`

```vue
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
```

- [ ] **Step 3: App.vue에 import 추가** — 기존 컴포넌트 import 블록(예: `ChartAnalysis` import 아래)에 추가

```javascript
import StockExplainer from './components/StockExplainer.vue'
```

- [ ] **Step 4: App.vue tabs 배열에 항목 추가** — `const tabs = [ ... ]` 배열에 기존 항목과 같은 형식으로 추가(라벨/키 컨벤션은 인접 항목을 따를 것; 키는 `explain`)

```javascript
  { key: 'explain', label: '상태 설명' },
```

- [ ] **Step 5: App.vue 컴포넌트 분기 추가** — 기존 탭 분기(`<NewsAnalysis v-else-if="active === 'news'" ... />`) 바로 아래에 삽입. `:code` 바인딩은 인접 분석 컴포넌트가 code를 받는 방식과 동일하게 맞출 것(인접 컴포넌트가 code prop 없이 STOCK_CODE 기본값을 쓰면 생략 가능).

```vue
              <StockExplainer v-else-if="active === 'explain'" key="explain" />
```

- [ ] **Step 6: 수동 검증**

```bash
# 백엔드 기동(server-starter 에이전트 또는):
PYTHONPATH=. ./venv/bin/python main.py   # 포트 8000
# 별도 터미널에서 프론트:
cd frontend && npm run dev
```
확인: "상태 설명" 탭 클릭 → 고지 배너 노출, 기술적/재무 서술 표시, 위험 신호가 붉게(warning)·주황(caution). 브라우저 DevTools에서 375/768/1024px 반응형 확인(모바일 1열 → 데스크탑 2열, 항목 높이 ≥44px). 엔드포인트 단독 확인: `curl localhost:8000/analyze/005930/explain`.

- [ ] **Step 7: 커밋**

```bash
git add frontend/src/api/client.js frontend/src/components/StockExplainer.vue frontend/src/App.vue
git commit -m "feat: 종목 상태 설명 패널(프론트) + 탭 연동"
```

---

## Self-Review

**Spec coverage:**
- 규칙 세트(RSI/MACD/MA/볼린저/유동성/PBR/PER/부채/ROE/배당) → Task 1 ✓ (볼린저 bb_state·유동성은 explain 지원하나 Task 2 라우트에서 미매핑 = 스펙의 "선택" 항목, 명시됨)
- severity 3단계·risks 재노출·disclaimer → Task 1 ✓
- 예측/모델/SHAP·buy·sell 미노출 → Task 2가 signal/confidence 제외(테스트로 강제) ✓
- 엔드포인트 → Task 2 ✓ (경로는 기존 `/analyze/<code>/*` 컨벤션에 맞춰 `/analyze/<code>/explain`; 스펙의 `/api/explain`보다 일관)
- Vue 패널·반응형 → Task 3 ✓
- 규칙엔진·기존 라우트 미변경(병존) → 신규만 추가 ✓

**Placeholder scan:** 코드 스텝 전부 실제 코드 포함. App.vue의 tabs/분기는 인접 패턴을 따르라는 지시 + 삽입 코드 명시(파일 내용이 가변적이라 정확 라인 대신 앵커 제공).

**Type consistency:** `explain(indicators, financials, liquidity=None)` 시그니처와 반환 키(technical/financial/risks/disclaimer, 항목 label/statement/severity)가 Task 1 정의와 Task 2/3 사용에서 일치. 상수명 일치.

**주의(경로 변경):** 스펙은 `/api/explain/<code>`였으나 기존 라우트 컨벤션(`/analyze/<code>/*`)에 맞춰 `/analyze/<code>/explain`으로 구현한다(더 일관·client.js 패턴 일치). 스펙 대비 의도된 조정.
