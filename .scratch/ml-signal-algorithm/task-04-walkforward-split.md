---
title: "T04: Walk-forward 분할기 (S3) — embargo + lockbox"
labels: [ready-for-agent]
---

# T04: Walk-forward 분할기 (S3)

## What to build

시간 순서를 지키는 walk-forward 학습/검증 분할을 만든다. 학습–검증 사이 embargo로 겹치는 창 누수를 막고, 마지막 구간은 lockbox로 봉인한다.

**End-to-end 동작:**
```
make_folds(date_range, embargo=5, folds=[...], lockbox=...) -> [(학습구간, 검증구간), ...]
```

## Acceptance criteria

- [ ] 시간 순서 고정 (무작위 셔플 금지)
- [ ] 학습 끝과 검증 시작 사이 **≥5거래일 embargo** 갭
- [ ] 여러 시기 walk-forward 폴드 생성 (예: 2022 / 2023 / 2024 검증)
- [ ] 마지막 구간 lockbox로 봉인 — 반환 폴드에서 제외 또는 별도 표시
- [ ] 검증 구간은 학습 구간보다 항상 미래

## Seam (테스트 필수)

- 검증 구간이 학습보다 항상 미래
- embargo 갭이 정확히 ≥5거래일
- lockbox가 일반 폴드에 포함 안 됨

## Blocked by

없음 (날짜 범위만 있으면 독립 구현·테스트 가능)

## User Stories

- 14, 15, 16, 17
