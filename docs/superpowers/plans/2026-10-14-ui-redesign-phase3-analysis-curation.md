# UI Redesign Phase 3: Analysis & Curation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Analysis & Curation screen (`AnalysisPanel.vue`) by separating proposal identification (compact central list) from proposal evaluation (dedicated inspection column with player, rationale, context, and editorial details), eliminating repetitive AI slop text from the list without breaking any of the 110 tests.

**Architecture:** Refactor `AnalysisPanel.vue` templates and scoped styles to strip long `rationale` and contextual paragraphs out of the middle column `.proposal-card` elements, while ensuring the right-column `.proposal-detail` prominently presents the media player, opening copy hook, full rationale, and contextual transcript; refine filter tabs into a compact segmented control.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Element Plus, CSS custom properties.

**Spec:** `docs/superpowers/specs/2026-10-14-ui-redesign-phase3-analysis-curation-design.md`

## Global Constraints

- All test selectors in `tests/analysis-panel.test.ts` must remain fully functional:
  - `data-action="select-focused"`
  - `data-action="generate-selected"`
  - `data-action="discard-proposal"`
  - `data-action="restore-proposal"`
  - `data-action="resume-analysis"`
  - `data-action="select-all-proposals"`
  - `data-action="clear-selection"`
  - `.proposal-open`, `.proposal-detail h3`, `.opening-copy`, `.topic-list button`, `.filter-pill-btn`, `.analysis-heading`.
- All 110 automated tests in the desktop test suite must remain green.

## Review Focus

- The proposal card in the central list must be compact (title, timestamp, duration, checkbox, discard action) with zero multi-line rationale repetition.
- The inspection panel must prominently display the proposal video, social hook opening text, full rationale, and transcript context.
- Overlapping proposals must visually display the overlap warning and disable selection properly.
- All filter tabs ("Ativas", "Descartadas", "Todas") must function smoothly as a segmented control.

---

### Task 1: Streamline Central Proposal List in `AnalysisPanel.vue`

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue`

**Interfaces:**
- Consumes: `proposals`, `filter`, `selection`, `discardedIds`
- Produces: Quiet, compact proposal list rows containing only title, timecode, duration, checkbox, and status tag.

- [ ] **Step 1: Inspect proposal card markup in `AnalysisPanel.vue`**
Identify where `p.rationale`, transcript excerpts, and heavy badges are rendered inside the central proposal list.

- [ ] **Step 2: Streamline `.proposal-card` template**
Remove inline multi-line rationale text from the list item so that the list functions as quick identification. Preserve `input[type=checkbox]`, `.proposal-open`, `time(p.start_us)`, `time(p.duration_us)`, overlap indicator, and `data-action="discard-proposal"` / `data-action="restore-proposal"`.

- [ ] **Step 3: Update `.proposal-card` styling**
Set compact padding, subtle hover surface `var(--color-surface-hover)`, clean border, and active selection state with `var(--color-surface-selected)` and `--color-text-primary`.

- [ ] **Step 4: Run analysis tests to verify**
Run: `cd desktop; npx vitest run tests/analysis-panel.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit streamlined proposal card**
```bash
git add desktop/src/components/AnalysisPanel.vue
git commit -m "feat(ui): streamline central proposal list to eliminate visual noise"
```

---

### Task 2: Enhance Inspection Column in `AnalysisPanel.vue`

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue`

**Interfaces:**
- Consumes: `inspectedProposal`, `sourceUrl`, `editorial`
- Produces: Polished editorial evaluation panel with player, social hook opening copy, rationale, and context.

- [ ] **Step 1: Structure `.proposal-detail` inspection layout**
Ensure clear hierarchy:
1. Header: Timecode range (`04:12 – 05:10`), duration, and proposal title (`h3`).
2. Player: Video preview with time boundaries.
3. Social hook: `.opening-copy` with hook duration and opening text.
4. Editorial justification: dedicated Rationale card/box.
5. Contextual transcript: before, quote, and after.
6. Primary action: `data-action="select-focused"`.

- [ ] **Step 2: Run analysis tests**
Run: `cd desktop; npx vitest run tests/analysis-panel.test.ts`
Expected: PASS.

- [ ] **Step 3: Commit inspection panel enhancements**
```bash
git add desktop/src/components/AnalysisPanel.vue
git commit -m "feat(ui): elevate proposal inspection panel with clear editorial evaluation"
```

---

### Task 3: Refine Segmented Filter Controls & Action Bar in `AnalysisPanel.vue`

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue`

**Interfaces:**
- Consumes: Filter states (`active`, `discarded`, `all`), selection counts
- Produces: Compact segmented filter pill control and clear generation action bar.

- [ ] **Step 1: Refactor filter tabs `.filter-pill-btn` into a compact segmented control**
Group into a quiet container with background `var(--color-canvas)` and border `var(--color-border-subtle)`. Active segment has background `var(--color-surface-raised)` and text `var(--color-text-primary)`.

- [ ] **Step 2: Ensure header / action dock has clear summary and button**
Summary displays `X propostas · Y selecionadas` and button `Gerar Y corte(s)` (`data-action="generate-selected"`).

- [ ] **Step 3: Run full vitest suite**
Run: `cd desktop; npm test -- --run`
Expected: All 20 test files, 110 tests pass.

- [ ] **Step 4: Commit controls refinement**
```bash
git add desktop/src/components/AnalysisPanel.vue
git commit -m "feat(ui): polish analysis segmented filters and generation action bar"
```

---

### Task 4: Complete Verification & Quality Gate

**Files:**
- Full suite: Vitest

- [ ] **Step 1: Execute complete test suite**
Run: `cd desktop; npm test -- --run`
Expected: 20 test files, 110 tests passed.

- [ ] **Step 2: Audit git status and diff**
Run: `git status`
Confirm clean workspace.
