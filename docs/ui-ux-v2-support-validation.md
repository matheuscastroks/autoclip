# UI/UX v2 — Supporting screens validation

## Phase 7 inventory

Base `dd0713a`. Added `TranscriptPanel.vue`, `useModalFocus.ts` and regression
tests for transcript, modal focus and App onboarding lifecycle. Modified Settings,
queue, onboarding, remaining icon consumers and their coordinating App bindings.
No backend, media pipeline, generated Python/TypeScript API contracts or Tauri
code changed. No credential values or media entered source control.

- **Transcript:** presentation extracted from ProjectWorkspace; search remains
  parent-owned across project tabs. Timestamps are native keyboard commands,
  playback marks the current passage, and text remains independently selectable.
  Original media retains ticket recovery and is unloaded on exit/unavailability.
- **Settings:** retained the already-flat three-category layout, existing fields,
  provider warnings and validation. Technical paths start collapsed; invalid
  required inputs reveal the correct category/disclosure and receive focus.
  Field/metadata typography uses the existing control/meta tokens.
- **Icons:** completed static Fluent migration in App, credentials, overlays and
  legacy job controls. Removed Lucide only after no consumers remained. Added
  twelve semantic allowlist entries; runtime names cannot load arbitrary SVG.
  Attribution/provenance is recorded in `THIRD_PARTY_NOTICES.md`.
- **Queue/setup:** replaced blur/glow/blue hardcodes with graphite/steel-blue
  tokens, retained installation/queue APIs, and constrained onboarding to an
  internally scrollable viewport. Active-count accessible name, pressed filter
  and model-choice states, Tab wrapping and opener focus restoration are covered.
- **CSS:** removed 83 obsolete rules from layouts/theme. Sixteen old class names
  were first checked against every source Vue/TypeScript file; mixed selectors
  retained their live branches, and negative pseudo-class selectors were skipped.

## Functional findings and rulings

Ruling: custom existing queue/setup overlays share only focus lifecycle; native
dialogs and Element Plus Drawers keep their own focus implementation. Cost: this
helper must remain covered when custom overlay contents change. Programmatic
focus on a noninteractive modal container does not draw an outer ring; keyboard
controls retain visible focus. A disappearing step command returns focus to the
modal rather than the background application.

The initial setup previously closed immediately when refreshed dependencies
became ready, hiding the credentials step. App now latches the opened flow until
explicit dismissal. Cost: an already configured user finishing resource setup
still sees the final handoff before closing; no automatic reopening after dismissal.

The newly reachable credentials step exposed a pre-existing false-success bug:
Vue emits were fire-and-forget, so failures still showed a validated/saved state.
Ruling: await parent-owned async credential callbacks, consistent with Settings,
instead of treating emission as persistence. Cost: the sole internal App consumer
was migrated from events to callback props. Pending controls prevent duplicate
submission/provider changes; failures stay visible with masked text for retry;
success clears the text and does not falsely claim connection validation.

Setup copy distinguishes local transcription/rendering from remote text-only AI;
decorative emoji, glow and unmeasured speed/accuracy claims were removed. No
provider, credential-storage or provisioning backend was changed.

## Automated evidence

RED→GREEN covered timestamp accessibility/playback tracking and cleanup,
collapsed technical paths with invalid-field recovery, static support SVGs,
accessible queue count, modal focus wrapping/restoration and removed-control
transitions, filter/model states, setup persistence after dependency readiness,
and failed credential storage without false success. Positive provider routing,
single pending submission and successful credential text clearing also ran.

Latest complete suite: **232 passed / 39 files**. Type check and build passed.
Lint: **0 errors / 19 inherited warnings**, down from 29 at Phase 6. Format check:
**7 inherited files**, none newly failing: client.ts, JobQueueItem.vue,
useJobQueue.ts, usePipelineSteps.ts, usePolling.ts, app-toast.test.ts and
openrouter-settings.test.ts in their existing locations. Only actively changed
files were formatted/fixed; unrelated baseline debt was preserved.

Production bundle: JS **460.31 kB / gzip 154.65**, CSS **485.24 kB / gzip 69.81**.
This measures bundle output, not runtime speed. `git diff --check` passed.

## Browser QA

Actual App/styles with disposable local API and synthetic media fixtures. All API
methods not explicitly simulated are denied; the only accepted credential value
in the success fixture is a fixed synthetic literal, never stored in Windows.
The fixture title explicitly identifies simulated QA, not the real application.

Transcript, local-resource Settings, queue and initial setup were checked at
**1920×1080, 1366×768, 1280×720, 1000×680 and 800×600**. No horizontal overflow
was measured. Compact transcript retained at least 149px of internally scrollable
text; original playback seek by Enter selected the correct timestamp/passage.
Search `importante` retained six matching passages across project tabs. Leaving
for Settings removed its player. Text computed as selectable.

Queue Tab wrapping, Escape and opener restoration were observed. Setup remained
inside each viewport and scrolled internally; installation success and failure
were simulated, without downloads. The credentials handoff remained open after
resource readiness, kept focus inside and used a password field. A rejected
synthetic key produced an inline error and no success; an explicitly allowed
synthetic success cleared text, updated readiness and allowed entering Library.

Screenshots are ignored local artifacts under `.runtime-tmp/ui-v2-qa/`:
`phase7-{transcript,settings,queue,onboarding}-<size>.png`,
`phase7-onboarding-credentials-800x600.png`,
`phase7-install-failure-800x600.png` and
`phase7-credential-{error,success}-800x600.png`.

Browser QA is not native Tauri, real installation, Windows credential storage,
remote-provider validation or real-media processing. Those were not executed;
neither were hosted CI, Python or Rust suites for this frontend-only phase.
Full cross-phase review, remaining prior-phase test gaps and final acceptance
audit remain **Phase 8**, not claimed complete here.

## Commits by responsibility

- `ff80a4c`: accessible synchronized transcript extraction.
- `185f223`: technical Settings disclosure and supporting icon registry.
- `7077d9c`: setup/queue identity, focus lifecycle and offline Fluent migration.
- `14bc982`: proven-unused editorial layout CSS removal.
- Credential persistence and attribution are committed separately after verification.
