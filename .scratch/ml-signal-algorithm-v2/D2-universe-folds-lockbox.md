---
title: "D2: 유니버스·기간·락박스 확대"
labels: [ready-for-agent]
phase: D
size: M
---

# D2: 유니버스·기간·락박스 확대

## What to build

v1의 12종목·2폴드를 확대해 "엣지 없음" 결론의 통계적 신뢰성을 확보한다. 진짜
point-in-time 유니버스 100~200종목, walk-forward 5폴드+, 락박스 홀드아웃.

**End-to-end 동작:**
```
get_universe(as_of, top_n=200)  # 각 시점 거래대금 상위 (ADR 0007 KRX 로그인)
make_folds(dates, folds>=5, embargo=5, lockbox=<최근 구간>)
```

## Acceptance criteria

- [ ] 유니버스 top_n을 100~200으로 확대, 시점별 재선정 유지(미래참조 없음)
- [ ] 기간 확대(예: 2015~2024)로 walk-forward 5폴드 이상 구성
- [ ] 락박스 구간을 별도 지정하고 학습·검증에서 제외 (`is_lockbox`)
- [ ] embargo(5거래일) 갭 유지
- [ ] 데모/러너가 확대 데이터셋으로 end-to-end 1회 완주

## Seam (테스트 필수)

- 폴드가 시간순·embargo·락박스 제외를 만족 (기존 `splits.py` 테스트 확장)
- 유니버스가 고정 목록이 아니라 시점별로 달라짐

## Blocked by

- D1 (수정주가 계약)
