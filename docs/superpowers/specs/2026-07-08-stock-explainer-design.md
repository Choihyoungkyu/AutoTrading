# 정직한 종목 상태 설명 + 리스크 표시 (Stock Explainer) — 설계

**작성일**: 2026-07-08
**상태**: 승인됨 (브레인스토밍 확정)
**배경**: ML 매수신호 v2가 STOP으로 종료(세 방향 모두 edge 없음, `docs/ml-signal-v2-c3-gate.md`).
edge 주장을 접고, 예측하지 않는 **의사결정 보조 도구**로 재구성한다.

## 문제 / 목표

사용자가 한 종목을 볼 때, "사라/팔라"가 아니라 **"지금 이 종목이 어떤 상태인가"를
투명한 규칙으로 서술하고 위험 신호를 표시**하는 도구가 필요하다. 예측·확률·매수등급은
내지 않는다. 검증되지 않은 edge를 신호처럼 제시하지 않는 것이 v1·v2 내내 지킨 원칙이다.

## 원칙

- **예측하지 않는다.** 현재 상태 서술 + 위험 표시만.
- 모든 응답에 고지: "현재 상태 설명이며 투자 권유가 아닙니다."
- **예측 모델(LightGBM)·SHAP은 UI에 노출하지 않는다.** edge 없음이 증명됐으므로(v2),
  연구 산출물로 문서에만 남긴다.
- 규칙엔진 추천(`recommendation_engine.py`)과 **병존**(ADR 0008), 기존 추천 UI 미변경.
- `chart_analyzer`가 이미 다는 `signal: buy/sell/hold` 태그를 **의도적으로 사용하지
  않는다**(그것이 접기로 한 예측). explainer는 숫자 지표만 받아 중립 서술로 변환한다.

## 아키텍처 (3층, 신규 코드 최소)

```
[Vue 새 패널] ──GET /api/explain/<code>──▶ [Flask route]
                                              │  기존 분석기 현재값 재활용
                                              ├─ chart_analyzer.analyze()      (숫자 지표)
                                              ├─ financial_analyzer.get_financial_metrics()
                                              └─▶ stock_explainer.explain()  규칙→서술/경고
```

point-in-time 파이프라인(KRX 로그인·수정주가·유니버스 재선정)은 **불필요** — 현재 상태
도구이기 때문. 기존 앱의 현재값 분석기를 그대로 쓴다.

## 컴포넌트 1: `src/analyzers/stock_explainer.py` (신규, 핵심)

순수 함수. 입력=현재 지표+재무 숫자, 출력=구조화된 서술/경고. 예측·모델 없음.

```
explain(indicators: dict, financials: dict, liquidity: dict | None = None) -> {
  "technical": [{"label", "statement", "severity"}],
  "financial": [{"label", "statement", "severity"}],
  "risks":     [{"label", "statement", "severity"}],   # caution/warning 재노출(방어 관점)
  "disclaimer": "현재 상태 설명이며 투자 권유가 아닙니다.",
}
```

- `severity` 3단계: `info`(중립 사실) · `caution`(주의) · `warning`(위험).
- `risks`는 technical·financial 중 `caution`/`warning`인 항목을 모아 재노출한다.
- 입력 필드가 없거나 0/None이면 해당 규칙은 **건너뛴다**(부분 데이터 허용).

### 규칙 세트 (투명·문서화, min-viable)

입력 지표(`chart_analyzer.analyze()` 산출 숫자에서 매핑):

| 영역 | 입력 | 규칙 | severity |
|---|---|---|---|
| RSI | `rsi` | <30 "단기 과매도 구간" / 30–70 "중립" / >70 "단기 과매수 — 과열 주의" | info / info / caution |
| MACD | `macd_line`,`macd_signal` | line>signal "상승 모멘텀" / line<signal "하락 모멘텀" | info |
| 추세 | `ma_20`,`ma_50` | ma_20>ma_50 "단기 상승 배열(정배열)" / 반대 "하락 배열(역배열)" | info |
| 볼린저 | `bb_state`(선택: "상단/중앙/하단") | 상단 "밴드 상단 — 과열 주의" / 하단 "밴드 하단 이탈" | caution |
| 유동성 | `liquidity.trade_value`(선택) | 임계 미만 "저유동성 — 슬리피지·상폐 주의" | **warning** |

입력 재무(`financial_analyzer.get_financial_metrics()`):

| 영역 | 입력 | 규칙 | severity |
|---|---|---|---|
| PBR | `pbr` | 0<pbr<1 "자산 대비 저평가 구간" | info |
| PER | `per` | per>0 표시 / per<=0 "적자 등으로 PER 산출 불가" | info / caution |
| 부채비율 | `debt_ratio` | >200% "재무 부담 높음" | **warning** |
| 수익성 | `roe` | roe<0 "자본 수익성 마이너스(수익성 부진)" | **warning** |
| 배당 | `dividend_yield` | >0 "배당수익률 N%" | info |

임계값은 이 표가 **단일 출처**다(코드 상수로 정의, 문서와 일치 유지). 판단이 개입하는
수치이므로 보수적으로 잡고, 변경 시 문서·테스트 동시 갱신.

## 컴포넌트 2: Flask 엔드포인트 (`src/api/routes.py`에 추가)

`GET /api/explain/<code>`:
1. `chart_analyzer.analyze(code)` → 숫자 지표. None이면 404/빈 응답.
2. `financial_analyzer.get_financial_metrics(code)` → 재무.
3. 두 결과에서 explainer 입력 dict 구성(+ 가능하면 유동성) → `explain()` → JSON 반환.

기존 라우트는 변경하지 않는다(신규 라우트만 추가).

## 컴포넌트 3: Vue 새 패널 (신규 컴포넌트)

- 종목 선택 시 `/api/explain/<code>` 호출 → "상태 설명" 패널 렌더.
- 기술적/재무 서술을 그룹으로, `warning`은 붉게·`caution`은 주황으로, 상단에 고지 배너.
- **반응형 표준 준수**(CLAUDE.md): 모바일 1열 → 태블릿/데스크탑 다열, 터치 타깃 ≥44px,
  모바일 폰트·패딩 규격.

## 데이터 흐름

`code` → route → (chart 지표 + 재무) → explainer 입력 매핑 → `explain()` →
`{technical, financial, risks, disclaimer}` → Vue 패널.

## 테스트

- **`stock_explainer.explain()` 순수 함수 (TDD 핵심):** 고정 지표/재무 입력 → 기대
  서술·severity·경고 검증. 경계값(RSI 30/70, 부채비율 200, roe 0, pbr 1) 각각.
  부분 데이터(필드 결측 시 규칙 스킵) 케이스. 고지 문구 존재.
- **엔드포인트:** 분석기를 목킹해 응답 구조(키·고지) 검증. 분석기 None 시 처리.
- 프론트: 수동 확인(반응형 375/768/1024px). 기존 테스트 스타일: `tests/test_financial.py`
  (고정값·`unittest.mock`).

## 범위 밖

- 예측·확률·매수/매도 등급(기존 규칙엔진 소관, **미변경**).
- 백테스트·ML 모델/SHAP UI 노출·point-in-time 파이프라인.
- 종목 스크리닝/순위(추후 별도) — 이번은 단일 종목 설명에 집중.

## 재사용 맵 (기존 인터페이스, 확인됨)

- `chart_analyzer.analyze(code)` → `rsi`, `macd{line,signal,histogram}`, `ma_20`, `ma_50`,
  `bollinger_band{upper,middle,lower}`, (+확장 항목). explainer는 이 중 숫자만 쓰고
  `signal/confidence`(예측)는 쓰지 않는다.
- `financial_analyzer.get_financial_metrics(code)` → `per`,`pbr`,`eps`,`bps`,`roe`,
  `dividend_yield`,`debt_ratio`,`as_of`.

## 참고

- v2 종료 근거: `docs/ml-signal-v2-c3-gate.md`, ADR 0008(규칙엔진 병존).
