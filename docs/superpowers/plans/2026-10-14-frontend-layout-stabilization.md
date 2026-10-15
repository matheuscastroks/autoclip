# Frontend Layout Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the AutoClip frontend one viewport-to-panel height contract so every existing project tab remains usable and scrollable after resize.

**Architecture:** `App.vue` owns viewport height, its existing wrappers pass available space to `ProjectWorkspace.vue`, and the active tab gives its child a bounded area. Transcript, Analysis and Cuts use that area for their split views and internal scroll. Preparation, Library and Settings scroll within their own content region. Remove the measured `--work-area-height` only after every consumer has migrated.

**Tech Stack:** Vue 3 SFCs, TypeScript, Element Plus splitter/scrollbar, existing CSS files, Vitest, Vite and Tauri 2.

**Spec:** `docs/superpowers/specs/2026-10-14-frontend-layout-stabilization-design.md`

## Global Constraints

- Preserve current actions, data contracts, polling and editorial behavior. Add no product feature or visual dependency in this delivery.
- Keep existing `data-action`, tab roles/ARIA attributes and Vue mount behavior.
- No fixed 520, 560 or 600 pixel panel height; media may have a bounded maximum size.
- Keep the global header and project tabs visible and put overflow in the designated content region.
- Preserve all unrelated work already present in the engine and Python tests; inspect `git status` before each commit and stage only task files.
- Use existing `desktop/src/layouts.css` and `desktop/src/theme.css` for shared structure; keep tokens and Element Plus theme intact.
- Save visual QA captures under ignored `scratch/layout-qa/`; do not stage media or `desktop/dist/`.

## File map

- `desktop/package.json`, `desktop/package-lock.json`: declare the missing `@eslint/js` development dependency compatible with ESLint 10.
- `desktop/src/App.vue`: mark the project screen for full-width/full-height treatment without changing navigation or polling.
- `desktop/src/layouts.css`: the shared height chain, tab panel sizing and removal of `--work-area-height` consumers.
- `desktop/src/theme.css`: reconcile later shell/page rules with that chain, preserving visual styling and responsive behavior.
- `desktop/src/components/ProjectWorkspace.vue`: one root, project header/tab/body layout and Transcript's inherited height; remove JavaScript measurement last.
- `desktop/src/components/AnalysisPanel.vue`: make the analysis splitter flex into allocated height.
- `desktop/src/components/ReviewPanel.vue`: make the review splitter flex into allocated height.
- `desktop/tests/workflow.test.ts`: guard tab transitions and preserved actions if a root wrapper change affects mounting.
- `scratch/layout-qa/`: ignored screenshots and a local QA log for this run.

## Review Focus

1. At 800×600, a long project title or wrapped tabs reduces the body height without hiding the tablist or bottom actions. Task 3 verifies this in the rendered app.
2. Empty Transcript/Analysis and unavailable preview media remain scrollable and reachable. Tasks 3–5 verify their rendered states.
3. Dragging an Analysis or Cuts splitter, then resizing, leaves each column and action reachable. Tasks 4–5 verify this in the rendered app.
4. The generation queue and portrait player stay within their allocated panel without a second document scrollbar. Task 5 verifies both populated states.
5. Library, Settings, loading and offline/error states remain usable even though the shell now clips document overflow. Tasks 2 and 6 verify these rendered states.

---

### Task 1: Restore the lint gate

**Files:**
- Modify: `desktop/package.json`, `desktop/package-lock.json`

**Interfaces:**
- Consumes: existing `desktop/eslint.config.js` import of `@eslint/js` and `eslint@^10.12.0`.
- Produces: a declared `@eslint/js` dev dependency in the same major version as ESLint, locked for `npm ci`.

- [ ] **Step 1: Reproduce the dependency failure.** Run `npm --prefix desktop run lint`; expect `ERR_MODULE_NOT_FOUND` for `@eslint/js` on the baseline checkout. Do not treat this as a source lint finding.
- [ ] **Step 2: Declare and lock the missing package.** Run `npm install --prefix desktop --save-dev "@eslint/js@^10"`. Inspect both package files; no other dependency should change except npm's required lock metadata. If network access is blocked, request the required sandbox escalation instead of substituting a package or changing ESLint rules.
- [ ] **Step 3: Re-run lint and check the lockfile.** Run `npm --prefix desktop run lint` and `npm ci --prefix desktop` followed by lint again. If lint reports source findings, record and address only findings required to get this existing gate working; do not change application behavior.
- [ ] **Step 4: Commit only package files (and any narrowly necessary lint fixes).** Run `git diff --check`, inspect `git status --short`, stage exact files and commit `fix(desktop): declare eslint js dependency`.

### Task 2: Pass viewport height through the app shell

**Files:**
- Modify: `desktop/src/App.vue`, `desktop/src/layouts.css`, `desktop/src/theme.css`
- Test: `desktop/tests/workflow.test.ts` (existing behavior coverage)

**Interfaces:**
- Consumes: existing `.app-shell > .global-header + .main-content > .page-content > .screen-content` hierarchy.
- Produces: a viewport-height column with `min-height: 0` through the main/page/screen chain; a project screen that uses available width; Library/Settings scroll in `.main-content`.

- [ ] **Step 1: Record a failing rendered check.** At 1280×720, inspect the current shell and a project with a long title; record viewport height, document `scrollHeight`, header bottom and available `.screen-content` height in `scratch/layout-qa/baseline.md`. This is the pre-change visual/geometry failure, not a jsdom CSS assertion.
- [ ] **Step 2: Implement the shell chain.** Give `.app-shell` `height: 100dvh`, column flex and hidden overflow; make `.global-header` nonshrinking; make `.main-content`, `.page-content`, `.screen-content` flex children with `min-height: 0`/`min-width: 0`. Use an explicit project-screen class or equivalent scoped state in `App.vue` so the editor fills the width while Library/Settings retain their comfortable maximum width. Reconcile the later rules in `theme.css` and the `max-width: 760px` wrapped header rule.
- [ ] **Step 3: Check the shell in the browser.** Re-run the measurements at 1280×720 and 800×600. Header remains visible, document does not acquire an outer vertical scrollbar, and Library/Settings/loading content can scroll inside the main region. Record actual results in `scratch/layout-qa/`.
- [ ] **Step 4: Run existing behavior tests.** Run `npm --prefix desktop run test:run -- tests/workflow.test.ts` and `npm --prefix desktop run check`; both must pass.
- [ ] **Step 5: Commit the shell only.** Check diff/status, stage the three listed source files and commit `refactor(desktop): give shell the viewport height`.

### Task 3: Make ProjectWorkspace and Transcript consume remaining height

**Files:**
- Modify: `desktop/src/components/ProjectWorkspace.vue`, `desktop/src/layouts.css`, `desktop/src/theme.css`
- Test: `desktop/tests/workflow.test.ts`

**Interfaces:**
- Consumes: Task 2's `.screen-content` height contract.
- Produces: a column root containing nonshrinking project heading/tablist and a flexing `.workspace-body > #project-panel`; Transcript splitter and segment region inherit panel height. Keep `--work-area-height` temporarily until Tasks 4–5 migrate all consumers.

- [ ] **Step 1: Preserve the tab contract with a focused test.** In `workflow.test.ts`, add an observable test that clicks Transcript, Analysis and Cuts, asserts the active `aria-selected`/`aria-labelledby` pair and confirms each expected view mounts; run the targeted test and observe failure only if the wrapper change breaks it. Avoid assertions on CSS strings.
- [ ] **Step 2: Add one root element to `ProjectWorkspace.vue`.** Put the existing heading, `.project-tabs` and `.workspace-body` under a single `.project-workspace` column. Keep props, emits, tab IDs, and v-if branches unchanged. In shared CSS make the root/body/panel flex through available height with `min-height: 0` and intentional overflow. Preparation scrolls in `#project-panel`.
- [ ] **Step 3: Convert Transcript.** Replace `.split-transcript-body`'s 520/450 pixel height and the scrollbar's `--work-area-height` max-height with flex/min-height rules. Preserve segment search, click-to-seek and empty state. Ensure the player region has a scroll path if it exceeds a short window.
- [ ] **Step 4: Verify rendered states.** At 1366×768 and 800×600, switch through Preparation, empty Transcript and populated Transcript; repeat with a long project title. Assert visually and by DOM geometry that header/tabs remain visible, segments scroll within their panel, and the empty state is reachable. Record screenshots/measurements in `scratch/layout-qa/`.
- [ ] **Step 5: Run tests and commit.** Run `npm --prefix desktop run test:run -- tests/workflow.test.ts`, `npm --prefix desktop run check`, then diff/status. Stage only listed files and commit `refactor(desktop): allocate project workspace height`.

### Task 4: Migrate Analysis to the panel contract

**Files:**
- Modify: `desktop/src/components/AnalysisPanel.vue`, `desktop/src/layouts.css`, `desktop/src/theme.css`
- Test: `desktop/tests/analysis-panel.test.ts`

**Interfaces:**
- Consumes: Task 3's bounded `#project-panel`.
- Produces: `.analysis-workspace` filling that panel, with heading/actions nonshrinking and `.analysis-layout.curation-3col-layout` using remaining height; topic, proposal and inspection columns scroll internally.

- [ ] **Step 1: Capture the current failure.** At 1280×720 with populated Analysis, note the splitter bottom relative to `#project-panel` and whether the Generate/selection actions remain reachable. Save the observation in `scratch/layout-qa/`.
- [ ] **Step 2: Remove Analysis's height guess.** Replace `height: calc(var(--work-area-height, ...) - 54px) !important` and `min-height: 560px !important` with flex sizing and `min-height: 0`. Reconcile shared `.analysis-layout` and desktop/narrow breakpoints so the heading, three scroll columns and dock fit the allocated panel. Keep existing selection and generation behavior.
- [ ] **Step 3: Inspect populated and empty/failed Analysis.** Check 1920×1080, 1280×720 and 800×600, including a dragged splitter and a window resize. Verify no clipped column/action, independent column scroll, keyboard access and no outer scrollbar; save captures.
- [ ] **Step 4: Run tests and commit.** Run `npm --prefix desktop run test:run -- tests/analysis-panel.test.ts`, `npm --prefix desktop run check`, inspect diff/status, stage exact source files and commit `refactor(desktop): fit analysis to project panel`.

### Task 5: Migrate Cuts and remove the measured height variable

**Files:**
- Modify: `desktop/src/components/ReviewPanel.vue`, `desktop/src/components/ProjectWorkspace.vue`, `desktop/src/layouts.css`, `desktop/src/theme.css`
- Test: `desktop/tests/workspace.test.ts`, `desktop/tests/review-integration.test.ts`

**Interfaces:**
- Consumes: Task 3's bounded panel and Task 4's Analysis migration.
- Produces: review splitter and queue/player regions sized by their containers; no `--work-area-height`, `measureArea`, `ResizeObserver` or `window.innerHeight` in the project layout.

- [ ] **Step 1: Capture the current Cuts failure.** With a populated review and queue, record the splitter, portrait player and decision actions at 1280×720 and after dragging its divider.
- [ ] **Step 2: Convert review and remaining CSS consumers.** Replace `ReviewPanel.vue`'s 600/520 pixel splitter heights with flex/min-height sizing. Convert all `--work-area-height` formulas in `layouts.css` for review list/details, generation queue and portrait media to container-relative scroll and bounded media sizing. Preserve responsive stacked layouts and the current selected cut behavior.
- [ ] **Step 3: Remove the measurement path.** Delete `workArea`, `areaHeight`, `measureArea`, listeners, observer, associated title watch and inline custom property in `ProjectWorkspace.vue`; retain the independent warning watch. `rg -n 'work-area-height|measureArea|window.innerHeight' desktop/src` must find no layout-height consumer.
- [ ] **Step 4: Inspect review states.** At 1920×1080, 1366×768, 1280×720 and 800×600, check populated/empty review, unavailable media, queue present, splitter drag and resize. Player, list, details and decisions remain reachable with expected internal scrolling. Save captures.
- [ ] **Step 5: Run tests and commit.** Run `npm --prefix desktop run test:run -- tests/workspace.test.ts tests/review-integration.test.ts`, `npm --prefix desktop run check`, inspect diff/status, stage exact source files and commit `refactor(desktop): fit review to project panel`.

### Task 6: Complete visual and automated validation

**Files:**
- Create: `scratch/layout-qa/results.md` (ignored local QA record)
- Test: all desktop source and test files through existing scripts

**Interfaces:**
- Consumes: Tasks 1–5's integrated layout.
- Produces: an evidence-backed handoff stating which rendered/native states passed, failed or could not be reproduced.

- [ ] **Step 1: Run automated gates.** Run `npm --prefix desktop run check`, `npm --prefix desktop run lint`, `npm --prefix desktop run format:check`, `npm --prefix desktop run test:run` and `npm --prefix desktop run build`. Fix task-caused failures in their owning files, rerun failed gates, and record exact outcomes. Do not rerun the Python suite unless a shared contract or backend file changed.
- [ ] **Step 2: Exercise the rendered matrix.** Capture Library, Settings, Preparation, Transcript, Analysis and Cuts at 1920×1080, 1366×768, 1280×720 and around 800×600. Include loading/empty/error cases when reproducible, long title, queue, unavailable preview, splitter drag and resize. Test bottom actions by mouse and keyboard; write pass/fail/not reproduced per case to `scratch/layout-qa/results.md`.
- [ ] **Step 3: Check native evidence.** If the local Tauri app can launch with its engine, repeat at least 1366×768 and 800×600 in a native window. Otherwise state that only browser rendering was checked; never label browser screenshots as native QA.
- [ ] **Step 4: Inspect the final diff.** Run `git diff --check` on this task's changed files, check `git status --short`, inspect commits and confirm `desktop/dist/`, media and unrelated engine/Python edits were not staged. Report remaining layout failures or untested states explicitly.

## Plan self-review

The six tasks cover the spec's lint prerequisite, single shell/workspace owner, Transcript/Analysis/Cuts migration, removal of the measured height, responsive/empty/error conditions and rendered QA. The five Review Focus cases have explicit rendered checks in their owning tasks. All tasks preserve current behavior and use the existing style files and test tools. No new frontend visual dependency or Python change is planned.
