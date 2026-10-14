# UI Redesign Phase 5: Visual QA, Accessibility & Final Verification Design Spec

## Context & Objectives

Phase 5 represents the culmination and quality gate of the complete UI/UX redesign of AutoClip Studio:
- **Phase 1**: Visual Foundations & Neutral Studio Tokens (`tokens.css`, `element-theme.css`, `theme.css`, `App.vue`, `components/*.vue`).
- **Phase 2**: Shell, Library & Preparation (`App.vue`, `ProjectLibrary.vue`, `PipelinePanel.vue`).
- **Phase 3**: Analysis & Curation (`AnalysisPanel.vue`).
- **Phase 4**: Review, Settings & Global Queue (`ReviewPanel.vue`, `SettingsPanel.vue`, `GlobalQueueModal.vue`).
- **Phase 5**: Automated QA guards, accessibility verification, and full-suite validation.

## Key Changes & Architecture

### 1. Automated Visual QA & Invariant Protection
- Expand `desktop/tests/visual-tokens.test.ts` to enforce:
  1. No legacy orange `#d97724`, `#c4671a`, or `217, 119, 36` in ANY file under `desktop/src/` (CSS, Vue, TS).
  2. No `@keyframes pulse` or aesthetic pulsing in any component or theme file.
  3. Strict Studio palette adherence in `tokens.css` (`#0D0F11`, `#16181B`, `#292D32`, `#E5E7EB`).
  4. Header shell height remains exactly 48px (`--header-height: 48px`).
  5. Library default remains list view (`viewMode = ref<'grid' | 'list'>('list')`).

### 2. Accessibility & Keyboard Navigation Audit
- Verify that keyboard navigation, ARIA attributes, and roles across interactive panels remain valid:
  - Header tabs (`role="tablist"`, `aria-selected`).
  - Analysis proposal cards (`tabindex="0"`, `role="button"`, `aria-label`).
  - Review cuts table (`tabindex="0"`, `role="checkbox"`, `aria-label`).
  - Settings steps keyboard arrows (`ArrowRight`, `ArrowLeft`, `Home`, `End`).

### 3. Verification Criteria
- All tests in `visual-tokens.test.ts` pass without errors.
- All 110 automated tests in the 20 test files pass with 0 failures, 0 warnings, and 0 regressions.
- Git working directory clean.
