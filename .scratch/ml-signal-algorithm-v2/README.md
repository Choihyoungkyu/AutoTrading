# ML 매수신호 파이프라인 v2 — 이슈 인덱스 & 일정

설계 문서: `docs/superpowers/specs/2026-07-08-ml-signal-v2-design.md`
원칙: **돈 벌 근거가 없으면 정직하게 멈춘다.** 단계 간 하드 게이트.

## 로드맵 (D → C → B → A)

```
D (검증 신뢰성)  ──GATE D→C──▶  C (저비용 실험)  ──GATE 라우팅──▶  B 또는 A
  D1 수정주가                     C1 재무 min-viable                B: 유니버스+생존편향
  D2 유니버스/폴드/락박스          C2 중소형주 min-viable            A: 재무 풀셋+뉴스
  D3 신뢰성 리포트+판정            C3 종합+라우팅 판정               (게이트 통과 arm만)
```

## 이슈 목록

| 이슈 | 제목 | 라벨 | 규모 | 선행 |
|---|---|---|---|---|
| D1 | 수정주가 반영 OHLCV | ready-for-agent | M | — |
| D2 | 유니버스·기간·락박스 확대 | ready-for-agent | M | D1 |
| D3 | 신뢰성 리포트 + D→C 판정 | ready-for-human | S | D2 |
| C1 | 재무 min-viable 실험 | ready-for-agent | M | D3(GO) |
| C2 | 중소형주 min-viable 실험 | ready-for-agent | S | D3(GO) |
| C3 | 실험 종합 + B/A 라우팅 판정 | ready-for-human | S | C1,C2 |
| B1 | 중소형주 유니버스 확대 | needs-triage | M | C3(C2승) |
| B2 | 생존편향 완화(상폐 포함) | needs-triage | L | C3(C2승) |
| B3 | 락박스 검증 + 판정 | ready-for-human | S | B1,B2 |
| A1 | 재무 피처 풀셋 | needs-triage | M | C3(C1승) |
| A2 | 뉴스 감성 피처 | needs-triage | L | C3(C1승) |
| A3 | 최종 검증 + 배포 판정 | ready-for-human | M | A1,A2 |

## 확정 일정 (2026-07-08 착수, 게이트 조건부)

| 스프린트 | 기간 | 내용 | 게이트 |
|---|---|---|---|
| S1 | 7/8 ~ 7/18 | Phase D (D1→D2→D3) | **7/18 D→C** |
| S2 | 7/21 ~ 7/31 | Phase C (C1·C2 병렬 → C3) | **7/31 라우팅** |
| S3+ | 8/4 ~ | 게이트 분기: B(≈2.5주) 또는 A(≈3주). 둘 다면 B→A | 각 단계 종료 게이트 |

- B·A는 조건부 — 게이트 통과 시 예상 소요이며 확정 일정 아님.
- 둘 다 진행 시 ~9월 중순 완료 예상.
- **게이트 STOP은 정상 결과.** 그 지점에서 일정 종료·재설계(v1처럼).
