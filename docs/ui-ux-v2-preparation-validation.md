# UI/UX v2 — Preparation validation

## Scope and baseline

Phase 4 only, based on clean HEAD `0cb97f6` on `poc-openshorts-gemini`.
The baseline had 189 passing tests in 33 files, 36 lint warnings, and ten
pre-existing Prettier failures. No concurrent writer was present.

No backend, Python contracts, scheduling, persistence, media pipeline, Tauri,
configuration, or dependencies changed. App remains responsible for API calls.
Phase 5 Analysis restructuring is not part of this delivery.

## Components and decisions

- Added `usePipelinePresentation.ts`: typed presentation/actions derived from
  existing jobs, revisions and analysis; reuses `latestJob`, `usePipelineSteps`
  and `useRenderFailures`, without persisting another domain state.
- Added `PipelineStatusHero.vue`: current condition, explanation, next action,
  visible recovery, and item-count or indeterminate progress, never an invented
  overall percentage. Rendering and validation are distinguished using the real
  `progress.phase` payload, while retaining legacy stage fallbacks.
- Added `PipelineStepList.vue`: three overview milestones; all eleven existing
  internal stages and their operational actions remain in technical details.
- Added reusable native `TechnicalDetails.vue`: keyboard-operated disclosure.
- Replaced the large `PipelinePanel.vue` presentation with coordination of these
  components. Removed its duplicate stepper, metrics cards and permanent player
  column. The original player is mounted only when details are expanded; close
  and unmount pause it, remove its source and reload it. `vRecoverMedia` remains.
- Added three statically compiled Fluent icons to the existing allowlist and
  regenerated component declarations through the existing build integration.
- Added `preparation.test.ts`; adapted workflow/review-integration assertions to
  the intentional milestone and on-demand-player contracts.

Current work outranks historical failures; history remains in the global queue.
The original video costs an extra disclosure expansion, avoiding a permanent
second column and closed-player loading. Generation requires completed analysis.
Final export requires valid final plus human approval, including legacy finals
without `final_state`. Already exported approved finals lead back to Cuts;
re-export remains available in technical details.

## Automated verification

Implementation commit: `cbf4aae` — `refactor(desktop): clarify preparation state and next actions`.

Final commands run locally:

| Command | Result |
| --- | --- |
| `npm --prefix desktop run check` | Passed |
| `npm --prefix desktop run lint` | 0 errors, 36 inherited warnings |
| `npm --prefix desktop run format:check` | Same 10 inherited failures; no changed file failing |
| `npm --prefix desktop run test:run` | 199 passed, 34 files |
| `npm --prefix desktop run build` | Passed |
| `git diff --check` | Passed |

The ten unchanged formatting failures are `src/api/client.ts`, `BaseModal.vue`,
`JobQueueItem.vue`, `ProviderSelector.vue`, `useJobQueue.ts`, `usePipelineSteps.ts`,
`usePolling.ts`, `useProposalSelection.ts`, `app-toast.test.ts` and
`openrouter-settings.test.ts` (under their existing component/composable/test paths).

Regression RED→GREEN covered historical failures versus active work, duplicate
cancel controls, lazy-player cleanup, incomplete-analysis generation, exported
next action, and the review finding below. Other cases cover queued/cancelling
work, interrupted recovery, real item counts and invalidated approved finals.

One independent read-only review found one Important issue: the first validation
fixture incorrectly used `stage: verify`, masking the engine's actual
`stage: render_final, phase: verify`. The representative regression failed first,
the presentation was corrected, then the complete 199-test suite passed again.
No Critical findings were reported. No second review cycle was requested.

Bundle: JS 464.71 kB / gzip 156.96; CSS 502.20 kB / gzip 72.37. Previous phase:
JS 467.28 / gzip 157.30; CSS 509.43 / gzip 73.39. These are bundle measurements,
not runtime performance claims.

## Browser evidence and limitations

Actual Vue App and global styles were exercised with disposable local API
fixtures and synthetic media, not private projects or remote AI calls. The
already-running local Vite server was reused without changing its lifecycle.

Preparation was inspected at 1920×1080, 1366×768, 1280×720, 1000×680 and 800×600.
No horizontal document overflow was measured. The minimum-window hero/action
remained visible; expanded details used the workspace's internal vertical scroll.
Long project titles truncate in the existing header.

At 800×600, additional fixtures covered pending transcription/analysis, preview
processing, import failure with visible cause/retry/local-file commands,
interrupted analysis with resume, final review, approved export and completed
export. At 1366×768, the real validation-phase payload displayed
`Validando versão final`. Native disclosure Enter opening/closing and one-player
on-demand/zero-player closed behavior were observed; cleanup calls are also
asserted by DOM tests. Full assistive-technology testing was not performed.

Screenshots are local ignored artifacts under `.runtime-tmp/ui-v2-qa/`:
`phase4-final-{1920x1080,1366x768,1280x720,1000x680,800x600}.png`,
`phase4-verify-1366x768.png`, `phase4-details-800x600.png`, and
`phase4-{transcribe,analysis,preview,failed,interrupted,review,approved,exported}-800x600.png`.

This is browser/fixture validation, not native Tauri, real-media processing,
paid-provider, real cancellation/resume, or hosted CI validation. Python and Rust
suites were not run because their code and shared behavior were unchanged.
Previously recorded Phase 2 queue-badge and Phase 3 modal/setup coverage gaps
remain outside this phase. No additional confirmed defect is left from this review.
