# UI Redesign Phase 4: Review, Settings & Global Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the Review Panel, Settings Panel, and Global Queue Modal to complete the Studio UI/UX redesign, eradicating all lingering animations, pulsing effects, and visual inconsistencies while keeping all 110 automated tests green.

**Architecture:** Update `ReviewPanel.vue`, `SettingsPanel.vue`, and `GlobalQueueModal.vue` scoped styling and templates to match the Linear-inspired dark studio aesthetic.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Element Plus, CSS custom properties.

**Spec:** `docs/superpowers/specs/2026-10-14-ui-redesign-phase4-review-settings-queue-design.md`

## Global Constraints

- All selectors and behaviors in the test suite must be strictly preserved:
  - `.cuts-filters button`, `.clip-item`, `.clip-preview > video`, `a[download]`, `[data-action=editorial-approve]`, `[data-action=editorial-reject]`, `[data-action=delete-clip]`.
  - `input[type=password]`, `[data-action=save-key]`, `data-settings-step`, `.model-chip`.
  - `.project-jump-btn`, `.cancel-job-btn`, `.queue-tab`, `.close-btn`.
- All 110 automated tests in the desktop test suite must remain green at each step.

---

### Task 1: Refine `ReviewPanel.vue` (Segmented Filters & Player Rail)

**Files:**
- Modify: `desktop/src/components/ReviewPanel.vue`

- [ ] **Step 1: Convert `.cuts-filters` into a segmented control**
  Wrap into a segmented container with canvas background, subtle border, and quiet chip states.

- [ ] **Step 2: Eradicate `@keyframes pulse` and pulsing animation**
  Remove `@keyframes pulse` and `animation: pulse 1.6s infinite ease-in-out` on `.item-state-dot[data-state='running']`. Keep dot solid and crisp.

- [ ] **Step 3: Polish player rail & editorial decision actions**
  Refine `.decision-btn`, `.preview-label`, `.clip-preview` 9:16 aspect ratio frame, and `.download-main-btn`.

- [ ] **Step 4: Run Review tests**
  Run: `cd desktop; npx vitest run tests/review-integration.test.ts tests/workspace.test.ts tests/cuts-table.test.ts tests/cut-delete.test.ts`
  Expected: PASS.

- [ ] **Step 5: Commit ReviewPanel updates**
  ```bash
  git add desktop/src/components/ReviewPanel.vue
  git commit -m "feat(ui): refine ReviewPanel filters, player rail and remove pulse animation"
  ```

---

### Task 2: Refine `SettingsPanel.vue` (Studio Nav & Diagnostic Cards)

**Files:**
- Modify: `desktop/src/components/SettingsPanel.vue`

- [ ] **Step 1: Neutralize navigation tabs & readiness cards**
  Refine `.settings-category-btn`, `.readiness-card`, and model chips to use neutral studio tokens without heavy saturation.

- [ ] **Step 2: Verify form controls and keyboard accessibility**
  Ensure secret password field, model picker, save button, and validation handlers work smoothly.

- [ ] **Step 3: Run Settings tests**
  Run: `cd desktop; npx vitest run tests/gemini-settings.test.ts tests/openrouter-settings.test.ts tests/desktop-polish.test.ts`
  Expected: PASS.

- [ ] **Step 4: Commit SettingsPanel updates**
  ```bash
  git add desktop/src/components/SettingsPanel.vue
  git commit -m "feat(ui): harmonize SettingsPanel tabs, readiness cards and inputs with studio theme"
  ```

---

### Task 3: Refine `GlobalQueueModal.vue` (Overlay & Task Cards)

**Files:**
- Modify: `desktop/src/components/GlobalQueueModal.vue`

- [ ] **Step 1: Refine modal overlay, header tabs, and task cards**
  Ensure segmented tab styling, dark studio background, and clean job cards.

- [ ] **Step 2: Run GlobalQueue tests**
  Run: `cd desktop; npx vitest run tests/global-queue.test.ts tests/project-queue.test.ts`
  Expected: PASS.

- [ ] **Step 3: Commit GlobalQueueModal updates**
  ```bash
  git add desktop/src/components/GlobalQueueModal.vue
  git commit -m "feat(ui): polish GlobalQueueModal overlay, segmented tabs and task cards"
  ```

---

### Task 4: Complete Verification Suite & Git Status

- [ ] **Step 1: Run full desktop vitest suite**
  Run: `cd desktop; npm test -- --run`
  Expected: 20 test files, 110 tests passed.

- [ ] **Step 2: Verify git status is clean**
  Run: `git status`
