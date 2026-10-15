# UI/UX v2 — Phase 3: library and project creation

## Changes and boundaries

- Added `components/library/ProjectListItem.vue`, reused by list and grid. A native opening button and a separate delete command replace nested interactive rows. Long titles truncate without invading state/count columns; full titles remain available by hover and accessible name.
- Kept existing search, state filtering, ordering and list-default state in `ProjectLibrary.vue`. Improved responsive select widths and keyboard focus when changing views. Empty library and no-results guidance remain distinct.
- Project terminal status now wins over stale `summary.stage`. A stage is shown only for a processing project. Generated counts remain “gerados”, not assumed final/approved/ready counts. Missing summaries show “Resumo indisponível”.
- Added `components/dialogs/NewProjectDialog.vue` with controlled visibility/form models, local/YouTube origins, keyboard source selection, configuration summary, dependency guidance and inline recoverable error.
- App retains picker, filename suggestion, API calls, automatic-preparation rules, refresh and project opening. The synchronous operation guard still prevents duplicate API creation. Picking and creating have distinct presentation states.
- Added a compiled Fluent Link icon; no new dependencies. Removed superseded dialog markup/scoped styles from App and duplicated list/grid markup/styles from the library.

No backend, contracts, queue, persistence, media pipeline, Tauri or session changes.
The existing project trash/active-job protection and processing eligibility remain.

## Decisions

The toolbar remains with its existing parent-owned state; extracting a one-use
toolbar would add event plumbing without useful responsibility separation. Cost:
the parent still contains toolbar markup.

The dialog remains native, with Element Plus action buttons and native radio-like
source commands. The latter avoid inherited important default-button backgrounds
hiding selection. No new UI library or important override was introduced. Cost:
native modal behavior still needs browser verification in addition to DOM tests.

Missing video tools block creation. Missing other setup retains the existing
ability to create without automatic preparation; supported backend settings and
API parameters were not changed.

## Automated regression evidence

Observed failure before implementation, then passing:

- Failed project showing an old analysis stage in list/grid.
- Missing summary without explicit unavailable state.
- Enter on delete bubbling into project opening.
- Creation failure lacking inline recovery while keeping picked file/name.
- Arrow-key source navigation absent.
- Pending picker incorrectly labelled as project creation.

Additional tests cover broken/replaced thumbnails, active-project deletion guard,
combined query/filter/order across views, supported URL single submission, invalid
host rejection, missing video tools and App import orchestration. Existing creation,
review and navigation tests remain in the full suite.

## Browser QA

Used actual App/components with disposable local API responses, synthetic video and
fake local paths. No real creation/import, filesystem picker, provider request or
paid AI was executed. Browser validation does not validate native Tauri behavior.

At 1920×1080, 1366×768, 1280×720, 1000×680 and 800×600:

- No document-level horizontal overflow.
- Long-title bounds remained before state bounds (at least 8px separation).
- Delete actions stayed inside the viewport.
- Dialog with long path plus recoverable error stayed inside the viewport, with
  footer visible and no horizontal scrolling.

The long-path check exposed inherited `.file-drop` flex centering: a 2456px selected
row overflowed a 560px dialog, whose scroll width reached 1507px. Scoped sizing and
min-width fixes reduced the row to approximately 477px and dialog scroll width to
its 558px client width. Full path remains in the native title; data is not shortened.

Verified grid availability, search-without-results, empty library, correct failure
label, legacy summary fallback, file/name retention on error, invalid URL disabled
submit, Cancel/reopen, source arrows and Escape. In a fresh opening, Cancel/Escape
returned focus to the triggering New Project command. HMR-created modal instances
were not used as proof of focus restoration.

Ignored evidence directory `.runtime-tmp/ui-v2-qa/`:

- `phase3-library-{width}x{height}.png` (five sizes).
- `phase3-library-final-1366x768.png` (stable final library).
- `phase3-grid-800x600.png`.
- `phase3-dialog-error-{width}x{height}.png` (five sizes, long path and error).
- `phase3-new-project-final-1366x768.png`.
- `phase3-no-results-1366x768.png`, `phase3-empty-1366x768.png`.

## Independent review and limits

One read-only fresh-context review found no confirmed Critical/Important defect.
Its long-path inspection request exposed the CSS issue above during browser QA;
it was corrected and remeasured. A separate pending-picker label regression was
also reproduced and corrected before the final full-suite run.

Deferred minor: extend automated native-modal lifecycle coverage (Cancel/Escape,
close/reopen and busy cancellation) and incomplete ASR/key setup with automatic
preparation disabled. Idle lifecycle was checked in the browser, but busy Escape
and the incomplete-setup variant were not manually exercised. This coverage gap is
not represented as validated by the DOM modal mocks.

Accepted review boundaries: App duplicate guards and async picker locks remain;
failed form values, terminal states/counts, delete isolation, import and compiled
icons were inspected. Queue badge accessibility remains deferred from Phase 2.
Native runtime, real media/providers, OS high contrast and full application
journeys remain outside this phase's evidence.

## Final gates

- `npm --prefix desktop run test:run`: **189 passed / 33 files**.
- `npm --prefix desktop run check`: passed.
- `npm --prefix desktop run lint`: 0 errors / 36 inherited warnings, down from 38.
- `npm --prefix desktop run format:check`: same 10 inherited files; no modified file failing.
- `npm --prefix desktop run build`: passed; JS 467.28 kB / gzip 157.30, CSS 509.43 kB / gzip 73.39.
- `git diff --check`: passed.

No Python/Rust suite was needed for frontend-only presentation changes. Hosted CI
was not queried; local checks are reported separately. No performance gain or native
runtime validation is claimed. Commits are recorded in the phase tracking plan.
