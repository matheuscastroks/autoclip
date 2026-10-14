# UI Redesign Phase 2: Shell, Library & Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the initial user flow by simplifying the global shell header (`App.vue`), making the project list the default view with streamlined metadata (`ProjectLibrary.vue`), and restructuring the preparation screen (`PipelinePanel.vue`) around the 3 pillars (Source, Processing State, Next Action) without breaking any existing tests.

**Architecture:** Refactor `App.vue` navigation styling and remove redundant library queue banner; update `ProjectLibrary.vue` default `viewMode` to `'list'` and clean up row hierarchy; reorganize `PipelinePanel.vue` to prioritize video source, real status, and primary action while preserving technical stage markers for test compatibility.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Element Plus, CSS custom properties.

**Spec:** `docs/superpowers/specs/2026-10-14-ui-redesign-phase2-shell-library-preparation-design.md`

## Global Constraints

- Default view mode for `ProjectLibrary.vue` must be `'list'`.
- All project row data attributes (`data-project-id`, `data-action="delete-project"`) must be preserved.
- All pipeline stages (`[data-stage=import]`, `[data-stage=transcribe]`, `[data-stage=analyze]`, etc.) and action buttons (`data-action="error-details"`, `data-action="retry-import"`, `data-action="replace-source"`) must remain functional.
- All 109 tests across all 20 test files must continue to pass without failure.

## Review Focus

- Project library list view renders properly by default and triggers `@open` and `@delete` events as expected by `workspace.test.ts` and `workflow.test.ts`.
- The duplicate queue banner is cleanly removed from `ProjectLibrary.vue` without affecting the header queue modal in `App.vue`.
- `PipelinePanel.vue` maintains player stability and clearly displays the next action button whether ready, processing, or in failure recovery.
- Responsive spacing in `PipelinePanel.vue` preserves video preview beside status and action.

---

### Task 1: Refactor Shell Header and Remove Library Queue Duplicate in `App.vue`

**Files:**
- Modify: `desktop/src/App.vue`

**Interfaces:**
- Consumes: Header navigation, queue modal trigger, project tabs
- Produces: Streamlined header with subtle dividers and single source of truth for background queue.

- [ ] **Step 1: Inspect and update header navigation in `App.vue`**
Reduce header height/padding to compact studio standard (`--shell-height: 48px`), replace strong borders with `--color-border-subtle`, and style project tabs with neutral hover and contrast-based active indicator.

- [ ] **Step 2: Remove redundant props passing or queue duplication to `ProjectLibrary` in `App.vue`**
Keep global queue indicator in the header; ensure clicking header queue opens `GlobalQueueModal`.

- [ ] **Step 3: Run test suite**
Run: `cd desktop; npm test -- --run`
Expected: PASS (all tests green).

- [ ] **Step 4: Commit shell changes**
```bash
git add desktop/src/App.vue
git commit -m "feat(ui): streamline shell header navigation and centralize queue indicator"
```

---

### Task 2: Refactor `ProjectLibrary.vue` to Default List View and Clean Metadata

**Files:**
- Modify: `desktop/src/components/ProjectLibrary.vue`
- Modify: `desktop/tests/visual-tokens.test.ts` or add library test assertions

**Interfaces:**
- Consumes: `Project[]`, `covers`, `busy`
- Produces: List view as default (`viewMode = 'list'`), streamlined rows with progressive disclosure of delete action, removal of duplicate queue banner.

- [ ] **Step 1: Update `ProjectLibrary.vue`**
- Set `const viewMode = ref<'grid' | 'list'>('list');`.
- Remove the `<aside class="global-queue-banner">` from the library template.
- Refine `.project-row` styling: compact height, clean typography, subtle hover surface (`var(--color-surface-hover)`), metadata clearly arranged (title, duration, stage, cuts, updated, delete action).
- Ensure delete button (`data-action="delete-project"`) has discrete appearance with title tooltip.

- [ ] **Step 2: Add test assertion for default list view in `visual-tokens.test.ts`**
Verify `ProjectLibrary` defaults to list view mode and contains project rows.

- [ ] **Step 3: Run tests**
Run: `cd desktop; npm test -- --run`
Expected: PASS (all tests green).

- [ ] **Step 4: Commit library changes**
```bash
git add desktop/src/components/ProjectLibrary.vue desktop/tests/visual-tokens.test.ts
git commit -m "feat(ui): set library view to default list and streamline project rows"
```

---

### Task 3: Redesign `PipelinePanel.vue` around the 3 Pillars (Source, Status, Next Action)

**Files:**
- Modify: `desktop/src/components/PipelinePanel.vue`

**Interfaces:**
- Consumes: `project`, `jobs`, `revisions`, `sourceUrl`
- Produces: 3-pillar layout (Source media, Processing status, Primary next action), secondary structured technical stepper.

- [ ] **Step 1: Reorganize layout of `PipelinePanel.vue`**
- Group top section into clear 3-pillar hierarchy:
  1. Source: Video original preview/player (`.pipeline-video`) with duration and source metadata.
  2. Status: Concise statement of current stage (e.g. "Importação concluída · Áudio em processamento" or "Vídeo pronto para análise"), real progress bar.
  3. Next Action: Dedicated primary button ("Iniciar análise" / "Ir para Análise" / "Ver cortes" / "Cancelar").
- Position failure recovery cards (`hasFailure`, `importRecovery`) directly within the action flow with `retry-import` and `replace-source`.
- Keep the technical pipeline stages (`[data-stage=...]`) and stepper in a structured, secondary clean container without visual competition.

- [ ] **Step 2: Verify all stage selectors and buttons are preserved**
Ensure `[data-stage=import]`, `[data-stage=transcribe]`, `[data-stage=analyze]`, `[role=progressbar]`, `[data-action=error-details]`, `[data-action=retry-import]`, `[data-action=replace-source]` are present and functional.

- [ ] **Step 3: Run Vitest test suite**
Run: `cd desktop; npm test -- --run`
Expected: PASS (all tests green).

- [ ] **Step 4: Commit pipeline redesign**
```bash
git add desktop/src/components/PipelinePanel.vue
git commit -m "feat(ui): redesign preparation panel around source, status and next action"
```

---

### Task 4: Complete Verification & Quality Gate

**Files:**
- Full suite: Vitest

- [ ] **Step 1: Execute complete test suite**
Run: `cd desktop; npm test -- --run`
Expected: 20 test files, 100% passed.

- [ ] **Step 2: Audit git status and diff**
Run: `git status`
Verify clean workspace with all commits matching the Phase 2 goals.
