# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 규칙 (AutoTrading 30일 해커톤)

### MVP 우선 원칙
- **Day 1-28**: 필수 기능만 (백테스팅 → 자동거래 → 대시보드)
- **Day 29-30**: 여유 있으면 추가 기능 (종목 분석) 고려
- **기능 추가 금지**: 일정 압박 시 추가 요청 기능은 미루기

### 위험 관리
- **실금 투자**: 10만원 손실 가능 → 코드 버그 최소화
- **키움 API**: 처음 사용 → 초반 학습곡선 높음
- **타이트 일정**: 과도한 기능 추가 시 모든 것이 실패할 수 있음

## 언어 규칙

- **코드**: 영어로 작성 (변수명, 함수명, 클래스명 등)
- **나머지**: 영어로 작성한 후 한국어로 번역한 내용 표시 (문서, 커밋 메시지, 이슈 설명, 주석 등)
- **커밋메시지**: 커밋 메시지는 한국어로, 한 줄 요약 + 변경 이유
# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.