# 주식 분석 시스템 프로젝트

## 에이전트 스킬

### 문제 추적 시스템

이슈는 이 저장소의 `.scratch/` 아래 마크다운 파일로 관리됩니다. `docs/agents/issue-tracker.md`를 참고하세요.

### Triage 라벨

표준 triage 라벨: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. `docs/agents/triage-labels.md`를 참고하세요.

### 도메인 문서

단일 컨텍스트 레이아웃: 저장소 루트에 `CONTEXT.md`와 `docs/adr/`. `docs/agents/domain.md`를 참고하세요.

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

## 5. Responsive Design Standards

**Mobile-first approach. All pages must work on smartphones and desktops.**

### Breakpoints
- **Mobile:** < 768px (phones)
- **Tablet:** 768px - 1023px
- **Desktop:** ≥ 1024px

### Base Styles (Mobile)
All styles start mobile-first (< 768px):
- Single column layouts by default
- Padding: 12-15px
- Font sizes: 12-14px for body, 18-20px for headers
- Touch-friendly buttons: min 44px height/width
- Simplified grids (1 column)

### Media Query Additions
Add enhancements at breakpoints using `@media (min-width: 768px)`:
```css
/* Tablet and desktop improvements */
@media (min-width: 768px) {
  .container { padding: 20px; }
  .grid { grid-template-columns: 1fr 1fr; }  /* 2-column */
  header h1 { font-size: 28px; }
}

@media (min-width: 1024px) {
  .price-chart { height: 380px; }  /* Larger charts */
}
```

### Common Components
- **Tables:** Stack columns on mobile, horizontal scroll fallback
- **Grids:** 1 col mobile → 2 col tablet → 3 col desktop
- **Cards:** Full width mobile, side-by-side on tablet+
- **Navigation:** Hamburger/stacked mobile, horizontal desktop
- **Charts:** Reduce height on mobile (250-280px), expand on desktop (320-380px)
- **Tooltips:** Adjusted width (200-250px mobile, 300-320px desktop)

### Testing Checklist
1. Test on actual mobile device or Chrome DevTools (375px, 768px, 1024px widths)
2. Verify touch targets (buttons, links) are ≥ 44px
3. Check table readability (font size, scrollable if needed)
4. Ensure chart legends don't overflow
5. Test form inputs are readable on mobile

### Don't
- Use desktop-only fixed widths
- Assume hover states work (mobile has no hover)
- Hide content from mobile without reason
- Use `vh` units for full-screen mobile layouts (address bar issues)