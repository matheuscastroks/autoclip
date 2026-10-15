# UI/UX v2 — Editorial analysis validation

## Phase 5 scope

Base `c14fc79`, clean checkout. Added `TopicNavigation`, `ProposalList`,
`ProposalItem`, `SelectionDock` and separate `ProposalInspectorDrawer` under
`desktop/src/components/analysis/`. `AnalysisPanel` coordinates existing
hash-bound selection/discard persistence rather than owning every presentation.
`ProjectWorkspace` supplies the existing authenticated media loader on demand.
`useProposalSelection` now enforces eligibility/discards for restored and new
selections; its existing overlap rules replace duplicate panel implementations.

The permanent layout has only topics and proposals. Below 1050px, topics become
a selector with the same discard/restore commands. The sole generation command
is in a nonfloating selection footer. Diagnostics remain a native disclosure.
Inspection never selects implicitly; selection never opens a player. The Drawer
uses the installed Element Plus 2.14.7, original video and ±15-second context,
transcript, rationale, opening, flags and recoverable media errors. It has no
final-approval controls. Closing invalidates pending requests and clears media.

Ruling: retain native controls/disclosure plus existing semantic tokens and static
Fluent icons; avoid another UI library or a second editorial state model.
Cost: presentation receives explicit props/events from the coordinating parent.

## Regression evidence

RED→GREEN: permanent original-player loading; checkbox/inspection separation;
missing selection eligibility/discard checks; partially discarded topics hidden
from discarded navigation; completed-analysis replacement leaving old inspection
open. Existing partial→complete inspection retention remains covered separately.

Tests also cover context playback/stop, invalid analysis, partial generation guard,
polling selection retention, overlap prevention, discard/restore, bulk selection,
obsolete async tickets, media failure/retry and five-criteria final review elsewhere.
No provider calls, transcription or rendering were performed by these tests.

Final local commands:

- `npm --prefix desktop run test:run`: **206 passed / 36 files**.
- `npm --prefix desktop run check`: passed.
- `npm --prefix desktop run lint`: **0 errors / 29 inherited warnings**, down from 36.
- `npm --prefix desktop run format:check`: **9 inherited failing files**; the
  actively changed selection composable was formatted, no drive-by cleanup.
- `npm --prefix desktop run build`: passed; JS **465.48 kB / gzip 157.22**,
  CSS **489.36 kB / gzip 70.72**. These are bundle sizes, not runtime benchmarks.
- `git diff --check`: passed before commit.

The nine remaining formatting files are client.ts, BaseModal.vue, JobQueueItem.vue,
ProviderSelector.vue, useJobQueue.ts, usePipelineSteps.ts, usePolling.ts,
app-toast.test.ts and openrouter-settings.test.ts in their existing locations.

## Browser QA

Actual App, components and styles with disposable local API/media fixtures.
List and Drawer inspected at **1920×1080, 1366×768, 1280×720, 1000×680, 800×600**.
No horizontal page/Drawer overflow was measured; the footer stayed inside every
viewport. On compact windows, the topic selector replaces the narrow column.
Checkbox selection kept zero players; inspection mounted one. Escape removed it
and restored focus to `.proposal-open`, with selection retained. Search and theme
filters composed; discard and restoration worked through the compact commands.
No-results state offers filter recovery. Expanded content scrolls independently.

Ignored local screenshots: `.runtime-tmp/ui-v2-qa/phase5-{analysis,drawer}-<size>.png`
at the five sizes. The screenshot video is synthetic color bars, not private media.
Browser QA does not validate native Tauri, actual engine cancellation/resume,
paid AI, an hour-long ticket expiry or assistive technology. Hosted CI and
Python/Rust suites were not run for this frontend-only phase. Prior phase coverage
limitations remain tracked in the plan. The final remaining-phase review occurs
after phases 6–8, rather than spawning reviewers for every extraction.
