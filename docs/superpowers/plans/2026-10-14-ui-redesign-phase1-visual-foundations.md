# UI Redesign Phase 1: Visual Foundations & Neutral Tokens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the visual foundations of AutoClip from an orange "AI slop" aesthetic into a sober, dense, monochrome-focused studio design (#0D0F11 canvas, #16181B surfaces, #292D32 selection, #E5E7EB primary action) without breaking any of the existing 106 automated tests.

**Architecture:** Update design tokens in `tokens.css`, neutralize Element Plus component styling in `element-theme.css`, remove aesthetic pulsing animations and glows in `theme.css`, eliminate gradients in `App.vue`, and systematically replace hardcoded orange properties in component scoped styles with semantic studio tokens. An automated test `visual-tokens.test.ts` validates token compliance and guarantees zero regression into orange accents.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Element Plus, CSS custom properties.

**Spec:** `docs/superpowers/specs/2026-10-14-ui-redesign-phase1-visual-foundations-design.md`

## Global Constraints

- `--color-canvas` must be `#0d0f11`.
- `--color-surface` must be `#16181b`.
- `--color-surface-raised` must be `#1c1f23`.
- `--color-surface-hover` must be `#23262a`.
- `--color-surface-selected` must be `#292d32`.
- `--color-action-primary` must be `#e5e7eb` with text `#111317`.
- No active interactive component or selection indicator may use `#d97724`, `#c4671a`, or `#f9a35c`.
- All 106 existing vitest tests in `desktop` must continue to pass without regression.

## Review Focus

- Any broken contrast on buttons or inputs when switching `--el-color-primary` from orange to `#e5e7eb` (text must remain legible with `#111317`).
- Hover states on secondary buttons must show subtle `#23262a` surface elevation without borders jumping.
- Checkboxes and radios must remain visible and checked without relying on `accent-color: #d97724`.
- Selection in `AnalysisPanel` proposals must clearly indicate active state through `--color-surface-selected` (#292d32) rather than 3px orange border.
- Vitest tests must not fail due to missing or renamed class selectors.

---

### Task 1: Create Token and Color Integrity Test

**Files:**
- Create: `desktop/tests/visual-tokens.test.ts`

**Interfaces:**
- Consumes: `desktop/src/tokens.css`, `desktop/src/element-theme.css`, `desktop/src/theme.css`
- Produces: Vitest unit test asserting the presence of new neutral studio tokens and the absence of `#d97724` and `#c4671a` in foundational styles.

- [ ] **Step 1: Write the failing test**

```typescript
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

describe('Visual Foundations Tokens', () => {
  const tokensPath = path.resolve(__dirname, '../src/tokens.css')
  const elementThemePath = path.resolve(__dirname, '../src/element-theme.css')

  it('defines the linear-inspired studio palette in tokens.css', () => {
    const tokens = fs.readFileSync(tokensPath, 'utf-8')
    expect(tokens).toContain('--color-canvas: #0d0f11')
    expect(tokens).toContain('--color-surface: #16181b')
    expect(tokens).toContain('--color-surface-selected: #292d32')
    expect(tokens).toContain('--color-action-primary: #e5e7eb')
  })

  it('does not define #d97724 or #c4671a as interactive accents in tokens.css or element-theme.css', () => {
    const tokens = fs.readFileSync(tokensPath, 'utf-8')
    const elementTheme = fs.readFileSync(elementThemePath, 'utf-8')
    expect(tokens).not.toContain('#d97724')
    expect(tokens).not.toContain('#c4671a')
    expect(elementTheme).not.toContain('#d97724')
    expect(elementTheme).not.toContain('217, 119, 36')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd desktop; npx vitest run tests/visual-tokens.test.ts`
Expected: FAIL due to tokens having old values (`#0b0d0e`, `#d97724`).

- [ ] **Step 3: Commit test file**

```bash
git add desktop/tests/visual-tokens.test.ts
git commit -m "test: add visual foundations token integrity test"
```

---

### Task 2: Implement Neutral Studio Palette in `tokens.css` and `element-theme.css`

**Files:**
- Modify: `desktop/src/tokens.css`
- Modify: `desktop/src/element-theme.css`

**Interfaces:**
- Consumes: Token values from design spec
- Produces: Studio dark color tokens with neutral action and focus ring.

- [ ] **Step 1: Update `tokens.css` with the neutral studio palette**

Replace `--color-canvas: #0b0d0e` with `#0d0f11`, `--color-surface` with `#16181b`, `--color-surface-raised` with `#1c1f23`, `--color-surface-hover` with `#23262a`, add `--color-surface-selected: #292d32`, replace `--color-accent` and all accent derivatives with `--color-action-primary: #e5e7eb` / neutral variants, and set `--color-border-focus` / `--color-focus-ring` to `#b8c0ca`.

- [ ] **Step 2: Update `element-theme.css` with neutral overrides**

Set `--el-color-primary` to `var(--color-action-primary, #e5e7eb)`, primary text to `#111317`, remove all `rgba(217, 119, 36, ...)` references, style primary buttons to `#e5e7eb` background with dark text, and neutralize tabs and selection borders.

- [ ] **Step 3: Run the token integrity test to verify it passes**

Run: `cd desktop; npx vitest run tests/visual-tokens.test.ts`
Expected: PASS.

- [ ] **Step 4: Commit token changes**

```bash
git add desktop/src/tokens.css desktop/src/element-theme.css
git commit -m "feat(ui): implement neutral studio tokens and element-theme overrides"
```

---

### Task 3: Eliminate Pulsing Animations, Brilhos, and Slop in `theme.css`

**Files:**
- Modify: `desktop/src/theme.css`

**Interfaces:**
- Consumes: Clean static indicator tokens
- Produces: CSS with no `@keyframes` pulsing orange glows or saturated selection highlights.

- [ ] **Step 1: Audit and neutralize keyframes in `theme.css`**

Remove or neutralize:
- `@keyframes pulse-subtle`, `@keyframes pulse-dot`, `@keyframes border-glow` containing `rgba(217, 119, 36, 0.7)` and orange box-shadows.
- Replace `.global-queue-indicator` and `.rendering-badge` pulsing effects with static, clean indicators.
- Replace any hardcoded `rgba(217, 119, 36, ...)` and `#f9a35c` rules with `--color-surface-selected` and `--color-text-primary`.

- [ ] **Step 2: Run test suite**

Run: `cd desktop; npm test -- --run`
Expected: All 19 test files pass.

- [ ] **Step 3: Commit theme cleanup**

```bash
git add desktop/src/theme.css
git commit -m "style(ui): eliminate aesthetic pulsing, glows and orange overrides in theme.css"
```

---

### Task 4: Eliminate Readiness Gradient and Slop in `App.vue`

**Files:**
- Modify: `desktop/src/App.vue`

**Interfaces:**
- Consumes: `--color-surface` and `--color-border-subtle`
- Produces: Solid studio readiness panel and neutral queue banner.

- [ ] **Step 1: Replace gradient in `App.vue`**

At line ~1034:
Replace `linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(217, 119, 36, 0.06) 100%)` with:
`background: var(--color-surface); border: 1px solid var(--color-border-subtle);`

- [ ] **Step 2: Neutralize global queue banner styling in `App.vue`**

Remove orange left-borders and pulsing effects, using `--color-surface-raised` and `--color-border-subtle`.

- [ ] **Step 3: Run test suite**

Run: `cd desktop; npm test -- --run`
Expected: PASS.

- [ ] **Step 4: Commit `App.vue` changes**

```bash
git add desktop/src/App.vue
git commit -m "style(ui): replace readiness gradient and neutralize queue banner in App.vue"
```

---

### Task 5: Eradicate Hardcoded Orange from Component Scoped Styles & Props

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue`
- Modify: `desktop/src/components/PipelinePanel.vue`
- Modify: `desktop/src/components/ReviewPanel.vue`
- Modify: `desktop/src/components/ProjectLibrary.vue`
- Modify: `desktop/src/components/ProviderSelector.vue`
- Modify: `desktop/src/components/SettingsPanel.vue`
- Modify: `desktop/src/components/GlobalQueueModal.vue`
- Modify: `desktop/src/components/OnboardingModal.vue`
- Modify: `desktop/src/components/ProjectWorkspace.vue`
- Modify: `desktop/src/components/ApiKeyField.vue`

**Interfaces:**
- Consumes: `--color-surface-selected`, `--color-border-strong`, `--color-text-primary`, `--color-focus-ring`
- Produces: Clean, monochrome studio styling across all components.

- [ ] **Step 1: Clean `AnalysisPanel.vue`**
Replace 3px solid orange left-border and orange background on proposals with `background: var(--color-surface-selected)` and `--color-text-primary`. Remove `accent-color: var(--color-accent, #d97724)`.

- [ ] **Step 2: Clean `PipelinePanel.vue`**
Remove `color="#d97724"`. Remove arbitrary `percentage="75"`. Replace orange active borders with neutral selection.

- [ ] **Step 3: Clean `ReviewPanel.vue`**
Remove `color="#d97724"`, remove orange glow box-shadows, replace active cut left border with `--color-surface-selected`.

- [ ] **Step 4: Clean `ProjectLibrary.vue`**
Remove 4px orange left border, replace with subtle neutral focus/selection indicator.

- [ ] **Step 5: Clean `ProviderSelector.vue` and `SettingsPanel.vue`**
Replace orange card borders and radio selections with `--color-border-strong` and `--color-surface-selected`.

- [ ] **Step 6: Clean `GlobalQueueModal.vue`, `OnboardingModal.vue`, `ProjectWorkspace.vue`, `ApiKeyField.vue`**
Replace `:color="'#D97724'"` and focus colors with `--color-focus-ring` / `#ECEEF0`.

- [ ] **Step 7: Run color scan to confirm zero active orange hex codes remain**

Run in PowerShell:
`Get-ChildItem -Path desktop\src -Recurse -Include *.vue,*.css,*.ts | Select-String -Pattern "#d97724|c4671a|#f9a35c|#d46b13" | Measure-Object`
Expected: 0 matches.

- [ ] **Step 8: Run full vitest test suite**

Run: `cd desktop; npm test -- --run`
Expected: All tests pass.

- [ ] **Step 9: Commit component style eradication**

```bash
git add desktop/src/components/*.vue
git commit -m "style(ui): eradicate hardcoded orange and slop across all desktop components"
```

---

### Task 6: Final Verification & Review Gate

**Files:**
- Test: Full desktop test suite

- [ ] **Step 1: Execute complete Vitest suite**
Run: `cd desktop; npm test -- --run`
Expected: 20 test files passed (including `visual-tokens.test.ts`), 100% tests green.

- [ ] **Step 2: Verify git status and diff**
Run: `git status`
Confirm clean workspace with only committed changes.
