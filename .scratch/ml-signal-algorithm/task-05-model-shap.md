---
title: "T05: 모델 학습 (LightGBM) + TreeSHAP 근거"
labels: [ready-for-agent]
---

# T05: 모델 학습 (LightGBM) + TreeSHAP 근거

## What to build

T02 라벨과 T03 피처로 LightGBM/XGBoost 이진 분류기를 학습하고, 매 예측마다 매수 확률과 TreeSHAP 근거를 반환한다.

**End-to-end 동작:**
```
predict("005930", as_of) -> {signal: "매수"/"매수 안 함", prob: 0.0~1.0,
                             reasons: [상위 SHAP 기여 피처, ...]}
```

## Acceptance criteria

- [ ] LightGBM/XGBoost 이진 분류 (트랜스포머 금지 — v1 범위 외)
- [ ] 출력: 매수/매수 안 함 신호 + 매수 확률(0~1)
- [ ] 매 예측당 TreeSHAP 상위 기여 피처를 근거로 반환
- [ ] SHAP는 상관이지 인과가 아님을 산출물에 표기
- [ ] T04 폴드 구조로 학습 (학습 구간에만 fit)

## Seam

모델 학습 자체는 라이브러리 동작이라 단위 테스트 대상 아님 — 결과는 T06 백테스트로 검증. 신호/확률/근거 반환 형식의 계약만 확인.

## Blocked by

- T01 (실데이터·유니버스), T02 (라벨), T03 (피처), T04 (분할)

## User Stories

- 1, 2, 3, 18, 19
