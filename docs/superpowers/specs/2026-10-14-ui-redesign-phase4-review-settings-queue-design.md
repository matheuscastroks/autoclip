# UI Redesign Phase 4: Review, Settings & Global Queue Design Spec

## Context & Objectives

Following the completion of Phase 1 (Visual Foundations & Studio Tokens), Phase 2 (Shell, Library & Preparation), and Phase 3 (Analysis & Curation), Phase 4 addresses the remaining functional surfaces of the AutoClip Studio:
1. **Review & Export (`ReviewPanel.vue`)**:
   - The cuts review workspace with table of cuts and 9:16 portrait player rail.
   - Refine the cuts filter into a compact segmented control consistent with `AnalysisPanel`.
   - Remove the aesthetic `@keyframes pulse` from `.item-state-dot` in running generation rows.
   - Refine the decision actions (Approve / Reject) and the download button to use clear high-contrast studio tokens without glow or saturation.
   - Ensure table layout, selection checkboxes, and bulk action toolbar have clean typography, borders, and paddings.
2. **Settings Hub (`SettingsPanel.vue`)**:
   - Multi-step settings workspace (Local resources, AI models, Cut duration).
   - Sidebar tab navigation with clear indicator dots and keyboard accessibility.
   - Forms, inputs, secret masking, and pickers matching the dark studio theme.
   - Clear diagnostic readiness cards for Whisper and FFmpeg.
3. **Global Queue Modal (`GlobalQueueModal.vue`)**:
   - Full overlay modal with backdrop blur and canvas background.
   - Segmented tab control for Active Jobs vs. Recent History.
   - Job cards with project navigation link, operation progress bars, and status pills.

## Key Changes & Architecture

### 1. `ReviewPanel.vue`
- Convert `.cuts-filters` to a segmented pill container:
  - Container: `background: var(--color-canvas)`, `border: 1px solid var(--color-border-subtle)`, `border-radius: var(--radius-control, 6px)`, `padding: 2px`.
  - Chips: transparent by default, hover gets lighter text, `.selected` gets `background: var(--color-surface-raised)`, `color: var(--color-text-primary)`.
- Eliminate `@keyframes pulse` and `animation: pulse ...` from `.item-state-dot[data-state='running']`. Use a solid, clear status indicator without distracting breathing animation.
- Ensure 9:16 player frame `.clip-preview` has clean subtle border `var(--color-border-subtle)` and soft neutral shadow.
- Preserve all existing selectors and data attributes (`data-action="delete-clip"`, `data-action="editorial-approve"`, `data-action="editorial-reject"`, `a[download]`, `.clip-item`, `.clip-preview > video`, `.cuts-filters button`).

### 2. `SettingsPanel.vue`
- Align category tabs (`.settings-category-btn`) with neutral studio styling:
  - Default: transparent surface, subtle border, muted text.
  - Selected: `background: var(--color-surface-raised)`, `border-color: var(--color-border-strong)`, `color: var(--color-text-primary)`.
- Neutralize readiness cards (`.readiness-card`):
  - Clean card surface with `var(--color-surface-raised)` and subtle border.
  - Green / warning accents confined strictly to icons and text badges.
- Model chips (`.model-chip`):
  - Clean borders with `var(--color-border-subtle)` and solid hover/selected surfaces (`var(--color-surface-hover)`, `var(--color-surface-selected)`).
- Preserve all selectors and interactive handlers (`input[type=password]`, `[data-action=save-key]`, `data-settings-step`, etc.).

### 3. `GlobalQueueModal.vue`
- Backdrop overlay: `rgba(0, 0, 0, 0.75)` with subtle backdrop-filter.
- Modal card: `background: var(--color-surface)`, `border: 1px solid var(--color-border-subtle)`, `border-radius: var(--radius-modal, 12px)`.
- Segmented tabs: clean segmented control for `Ativas` vs `Histórico recente`.
- Job cards: clean division lines, progress bars with neutral action primary fill, clear project jump link.

## Test & Verification Plan

- Must pass all tests in `desktop/tests`:
  - `tests/review-integration.test.ts`
  - `tests/workspace.test.ts`
  - `tests/global-queue.test.ts`
  - `tests/cut-delete.test.ts`
  - `tests/cuts-table.test.ts`
  - `tests/gemini-settings.test.ts`
  - `tests/openrouter-settings.test.ts`
  - `tests/desktop-polish.test.ts`
  - Full suite: 20 test files, 110 tests passing.
