# Triage 라벨

이 프로젝트는 5가지 표준 triage 라벨을 사용해 이슈의 생명주기를 관리합니다.

## 라벨 참고표

| 라벨 | 의미 | 다음 상태 |
|------|------|---------|
| `needs-triage` | 유지보수자의 평가 및 우선순위 지정 필요 | → `needs-info` 또는 `ready-for-agent` 또는 `wontfix` |
| `needs-info` | 리포터의 추가 정보 대기 중 | → `needs-triage` (정보 제공 후) 또는 `wontfix` |
| `ready-for-agent` | 완전히 명확함. AI 에이전트가 인간 맥락 없이 처리 가능 | → `in-progress` (할당 시) |
| `ready-for-human` | 인간 개발자가 구현할 준비 완료 (설계 결정, 도메인 전문성 필요) | → `in-progress` (할당 시) |
| `wontfix` | 처리하지 않을 것 (중복, 범위 외 등) | (최종 상태) |

## 사용법

- 이슈 마크다운 파일의 YAML 프론트매터에 라벨 적용
- 이슈가 triage를 거치며 진행될 때마다 라벨 업데이트
- 범위 외거나 중복된 이슈는 `wontfix` 사용

## 예시

```markdown
---
title: "실시간 주가 스트리밍 추가"
labels: [wontfix]
wontfix-reason: "V1 범위 외. V2 계획됨."
---
```
