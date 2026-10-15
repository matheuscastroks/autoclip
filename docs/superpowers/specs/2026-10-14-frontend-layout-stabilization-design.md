# AutoClip frontend layout stabilization — design spec

**Date:** 2026-10-14
**Branch:** `poc-openshorts-gemini`
**Scope:** First usable delivery of frontend stabilization (baseline and shared layout contract)
**Status:** Proposed for written review

## Purpose and constraints

Make the existing desktop workflow fit its available window and scroll predictably. The user should be able to reach every control in Preparation, Transcript, Analysis and Cuts after opening a project, switching tabs, resizing the window or dragging a splitter. Preserve current actions, data contracts, polling and editorial behavior. Add no product feature or visual dependency in this delivery.

The current parent calculates `--work-area-height` from `window.innerHeight` and an element's top edge. Children then combine it with their own viewport calculations and minimum heights. The contract below replaces those competing measurements with one chain of available height. Component splitting and broad CSS consolidation are subsequent deliveries.

## Verified baseline and prerequisite

At the start of this design, `npm --prefix desktop run check` passed, Vitest passed 112/112 tests in 20 files, `npm --prefix desktop run build` passed, and `pytest -m "not real_media" -q` passed 212 tests with one deselected. The working tree was clean. `npm --prefix desktop run lint` could not start: `desktop/eslint.config.js` imports `@eslint/js`, while `desktop/package.json` does not declare it. Add the missing development dependency to `desktop/package.json` and its lockfile in the baseline task, then run lint again. Record any lint findings separately from this missing-package failure.

The earlier `docs/superpowers/plans/2026-10-14-analysis-panel-ergonomics-redesign.md` is historical input. Its proposed `calc(100vh - ...)` plus a large minimum height does not satisfy this contract and must not be applied as the layout solution.

## Ownership and sizing contract

`App.vue` owns the viewport through the existing `.app-shell` root. It is a column occupying `100dvh`; `.global-header` retains its natural token-defined height and does not shrink. `.main-content` receives the remaining height and has `min-height: 0` and `min-width: 0`. The viewport root contains scrolling within its descendants rather than extending the document. The global header stays visible.

The existing `.page-content` and `.screen-content` wrappers pass remaining height down with flex layout and `min-height: 0`. On project pages, `.page-content` uses the available width, allowing the editor to fill the main area. Library and Settings retain comfortable maximum content widths and scroll within the main region. Initial loading, setup/readiness, empty and error states remain reachable and do not depend on a project being mounted. No new `AppShell.vue` component is required for this delivery; `App.vue` is the shell owner.

`ProjectWorkspace.vue` has a single column root around the existing project heading, tablist and `.workspace-body`. The heading and tabs take their content height; `.workspace-body` takes the rest with `flex: 1`, `min-height: 0`, `min-width: 0` and controlled overflow. `#project-panel` fills `.workspace-body`. The root must tolerate a wrapped project title or tabs at narrower widths without changing a hardcoded offset. Remove `workArea`, `areaHeight`, `measureArea`, their resize listeners/observer and the injected `--work-area-height` after all consumers have been converted.

The tab panel is the boundary for the active view. Preparation can scroll as a document inside it. Transcript, Analysis and Cuts occupy the panel height where their split views are present; the relevant content columns own vertical scrolling. Parent wrappers do not create a second vertical scrollbar around those columns. Where content or splitter minimum widths cannot fit, the view offers horizontal access or a responsive stacked layout without hiding controls.

| Active area | Fixed within its available area | Scroll owner |
| --- | --- | --- |
| Library / Settings / loading | Global header | Main content region |
| Preparation | Global header, project heading, tabs | Active project panel |
| Transcript | Global and project navigation, transcript heading | Transcript segments; player area if its content needs it |
| Analysis | Global and project navigation, analysis heading and actions | Topic list, proposal list and inspector independently |
| Cuts | Global and project navigation | Cut list/details and player rail as needed |

No panel should require a fixed 520, 560 or 600 pixel height to render. At short viewport heights, the allocated editor area may be small; essential controls remain accessible through their view's scroll region. Splitter panel width constraints may remain where needed for legibility, but must not force inaccessible content on a narrow window.

## CSS and component boundaries for this delivery

Update the existing shell and wrapper rules in `desktop/src/layouts.css` and `desktop/src/theme.css` in place. Resolve the conflicting `.app-shell`, `.main-content`, `.page-content`, `.workspace-body`, `#project-panel` and tab-view rules so each sizing decision has one effective owner. Keep visual tokens and Element Plus theming intact. Remove or replace only viewport-height formulas and overrides that conflict with the contract; defer broad selector renaming and style migration.

In `ProjectWorkspace.vue`, make the Transcript splitter and segment scrollbar inherit allocated height rather than `520px` or `max-height="calc(var(--work-area-height, ...))"`. In `AnalysisPanel.vue`, let the three-column splitter flex within `.analysis-workspace` with `min-height: 0`, removing its `calc()` and `560px` minimum. In `ReviewPanel.vue`, let the review splitter use the tab panel's height instead of `600px`/`520px`. Convert the `--work-area-height` consumers in `layouts.css`, including generation queue and player sizing, to container-relative sizing or bounded media dimensions. Preserve existing responsive breakpoints where their behavior remains useful.

This delivery does not extract components or composables, change selection eligibility, change `makeDecision()`, change the three-second polling strategy, or touch Python engine code. Those concerns require separate behavior analysis and tests.

## Behavior and failure cases

Switching tabs keeps current Vue mount behavior and existing tab accessibility attributes. Opening and closing a queue, loading state, empty transcript or analysis, missing preview media and offline/error state must not trap content outside a scrollable region. When a long project title wraps or browser text is enlarged, the workspace body takes the reduced remaining height. Resizing the window or moving a splitter must not require a JavaScript remeasurement for vertical layout. Any necessary horizontal overflow must be visible and keyboard reachable.

## Verification and acceptance

1. The baseline lint dependency is declared and `npm --prefix desktop run lint` executes. Run `npm --prefix desktop run check`, `npm --prefix desktop run format:check`, `npm --prefix desktop run test:run` and `npm --prefix desktop run build`; record outcomes. Run the backend CI suite only if frontend changes touch a shared contract or a separate backend risk is discovered, since its current baseline is known.
2. Add focused tests for the workspace contract and tab transitions where observable behavior changes. Keep selectors and `data-action` hooks used by existing tests. DOM assertions alone are insufficient to prove fit or scrolling.
3. Inspect rendered Library, Settings, Preparation, Transcript, Analysis and Cuts at 1920×1080, 1366×768, 1280×720 and a compact window around 800×600. Include loading/empty/error states where reproducible, a long project title, populated Analysis/Review, a dragged splitter, and a resize while a tab is open. Capture screenshots or a short recording. If native Tauri cannot be run locally, report browser verification explicitly and leave native fit unclaimed.
4. For each inspected state, confirm the header and project tabs stay visible, content reaches the bottom without clipping, and the expected region scrolls without duplicate page/panel bars. Verify the player and decision actions remain reachable with mouse and keyboard. Record any state that cannot be reproduced rather than counting it as passed.
5. Check `git diff` for unrelated edits and generated `dist/` content before handoff. The deliverable is a working layout migration with a clear verification record, not a CSS-only patch presented as visually validated.

## Rollout boundary

Ship this as one reviewable frontend change with the lint prerequisite and layout contract. Component decomposition, CSS layer consolidation and selection/domain cleanup follow only after the layout is stable, using their own plans and regression checks.
