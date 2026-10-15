# UI/UX v2 — Foundation validation

## Scope and commits

This increment implements phases **0 and 1 only**, not the complete redesign.
Rail, contextual header, component extraction and the two-region Analysis layout
remain queued behind the foundation acceptance gate.

- `992718e`: baseline, ownership/state matrix and phased tracking.
- `4add758`: graphite/steel-blue tokens, typography and accessible control theme.
- `db49719`: statically compiled Fluent icons and a real-consumer sample.

No backend, Python contracts, scheduler, media pipeline, persistence or Tauri
changes. Existing event handlers, selection rules and editorial gates are intact.

## Component and dependency inventory

Created `components/ui/AppIcon.vue`, its typed `icons.ts` allowlist, icon module
declarations and focused icon/contrast tests. Modified App navigation/actions,
ProjectLibrary, one Analysis playback command and GlobalQueueModal icon consumers.
No Vue components were removed or extracted in this increment.

Updated tokens.css, element-theme.css and shared typography in theme.css. Replaced
the primary-button hardcoded overrides with supported Element Plus variables;
other historical CSS remains for consumer-by-consumer migration. Updated Vite,
package manifests and generated component declarations. Existing Lucide remains
installed for unmigrated consumers; it is not prematurely removed.

Installed build-only, exact versions: `unplugin-icons@24.0.0` and
`@iconify-json/fluent@1.2.60`. Verified Element Plus **2.14.7** locally. Vue compiler
is `vue3`, automatic icon installation disabled. AppIcon imports a fixed local
set, uses no runtime provider or dynamic SVG input, and rejects inherited or
unknown runtime names. Sizes are 16/20/24 px, regular by default, filled for
supported active navigation. Decorative icons are hidden from assistive technology;
informative icons receive a label without an additional keyboard focus stop.

References: [unplugin-icons integration](https://github.com/unplugin/unplugin-icons),
[Microsoft Fluent System Icons](https://github.com/microsoft/fluentui-system-icons).

## Foundation tokens

| Semantic role | Value |
| --- | --- |
| Canvas / surface / raised | `#101316` / `#171D22` / `#202930` |
| Hover / selected | `#283540` / `#304451` |
| Subtle / strong / control border | `#34434E` / `#657E8E` / `#778E9E` |
| Primary / secondary / muted text | `#EDF1F4` / `#A5B5BE` / `#9FB0BA` |
| Primary / hover action | `#AFC6D5` / `#C5D9E6` |
| Action foreground | `#16232D` |
| Focus | `#AFC6D5` |
| Font scale | 22 / 16 / 14 / 13 / 12 px |
| Default control height | 34 px |
| Space scale | 4 / 8 / 12 / 16 / 24 / 32 px |

Segoe UI Variable → Segoe UI → system-ui is unchanged. Existing 6 px control and
8 px panel radii and functional success/warning/error tokens are retained.
Scoped legacy typography/layout is not claimed to be fully migrated yet.

The proposed muted `#91A3AF` gave only **3.89:1** on selected surfaces. Its adjusted
value gives **4.53:1**. Tests exercise all three text tokens on five surfaces,
focus ≥3:1 and primary text ≥4.5:1. Measured primary label: 9.04:1, hover 11.00:1,
focus/selected 5.73:1, control border/raised 4.33:1. Decorative separators are not
represented as accessible control boundaries.

Independent review caught compositions that token-only tests could not:

- Filled info tag: white on a light background, 2.11:1. The same white foreground
  was unsuitable for other filled semantic tags. Browser assertions failed before
  the fix and passed afterward: info 7.58, primary 9.04, success 8.32, warning 9.59,
  danger 5.78. The fix changes the semantic text variable, preserving consumer
  overrides and labels.
- Disabled primary button: white on light blue, 1.45:1. Even though disabled
  controls are contrast-exempt, it now uses secondary text on selected surface,
  4.81:1 at full opacity, with its native disabled state preserved. This was also
  reproduced and remeasured in the browser before/after the fix.

## Automated checks

| Command | Baseline | Foundation |
| --- | --- | --- |
| `npm --prefix desktop run check` | Pass | Pass |
| `npm --prefix desktop run test:run` | 146 / 27 files | 172 / 29 files, including rerun after review fixes |
| `npm --prefix desktop run lint` | 0 errors, 40 warnings | 0 errors, 38 inherited warnings |
| `npm --prefix desktop run format:check` | 11 failing files | 10 inherited, untouched failing files |
| `npm --prefix desktop run build` | Pass | Pass; final rerun recorded in phase tracker |

The old palette assertion in visual-tokens.test.ts was intentionally updated and
that changed test file formatted. No unrelated files were reformatted. Remaining
format failures: client.ts, BaseModal.vue, JobQueueItem.vue, ProviderSelector.vue,
useJobQueue.ts, usePipelineSteps.ts, usePolling.ts, useProposalSelection.ts,
app-toast.test.ts and openrouter-settings.test.ts.

Existing journey, workflow, analysis, workspace, cuts/Drawer, review, settings,
onboarding and global queue regressions ran as part of the full suite. This is
not an assertion that all eight end-to-end journeys were manually repeated.
No Python suite was run because there were no shared/backend changes. Hosted
Linux CI was not queried: GitHub CLI was unavailable; local results are reported
separately rather than presented as hosted CI success.

## Bundle and offline icons

Production comparison before the final small contrast adjustments:

| Asset | Baseline | Foundation sample |
| --- | ---: | ---: |
| JavaScript | 450.39 kB / gzip 151.93 | 463.61 kB / gzip 155.52 |
| CSS | 509.79 kB / gzip 73.35 | 511.25 kB / gzip 73.62 |

The JS gzip increase was 3.59 kB with both icon families temporarily present.
This measures bundle size, not startup/rendering performance. Final build output
is recorded in the phase tracker.

All 16 allowed icons rendered as inline SVGs with real paths, no image/use
resources, in a fixture CSP blocking nonlocal script/image/connect requests.
That verifies no external icon-provider dependency; it is not an OS airplane-mode
test or a claim that unrelated app integrations work offline.

## Browser evidence and limits

Actual Vue components were mounted with synthetic props and local FFmpeg-created
source/preview/final files. No private media, AI calls, credentials or real jobs
were used. The scenario selector and control showcase are QA-only, not application
features. Evidence is ignored locally under `.runtime-tmp/ui-v2-qa/`:

- `baseline-*-1366x768.png`: populated/empty library, processing, failure, Analysis,
  Settings, Cuts and long-title Drawer.
- `phase1-library-{width}x{height}.png` and `phase1-drawer-{width}x{height}.png`:
  1920×1080, 1366×768, 1280×720, 1000×680, 800×600. DOM geometry confirmed no page
  horizontal overflow; Drawer footer visible, no internal horizontal overflow,
  one player. Preview metadata was 540×960, final 1080×1920.
- `phase1-final-1366x768.png`: final, five unchecked editorial criteria and disabled
  approval. Escape/button closing released the player.
- `phase1-controls-icons-1366x768.png`, `phase1-queue-1366x768.png`,
  `phase1-settings-800x600.png`, plus empty/processing/failure/Analysis snapshots.

Pointer commands had no retained focus ring; Tab produced visible focus. Native
checkbox accent used the action token. Editable text remained selectable. Queue
names/close commands stayed accessible. Browser reconnection was needed during
QA; only the disposable test tab was operated.

Not manually exercised: native Tauri, OS forced-colors/reduced-motion modes,
installation/provisioning, URL/file creation, remote providers, real job
cancellation/resume, real export or hour-long ticket expiration. These are later
journey acceptance checks, not implied by the fixture screenshots.

## Known issues and next gate

The next phase is the compact rail/context header/project tabs. Analysis is still
the current three-region layout until phase 5; no proposal Drawer was introduced
prematurely. Remaining Lucide/scoped CSS consumers migrate in their own phases.
The baseline library prefers `summary.stage` in its label even for terminal
project status; the fixture exposed a failed row labelled “Analisando temas”.
Reconcile that presentation in phase 3 without inventing new API counts.

At 800×600, the current library can overlap long row titles with status/counts
despite no outer horizontal overflow. This was observed visually, not dismissed
based on DOM width checks. Resolve it in the Library layout phase; this increment
does not declare the entire application's compact-window UX complete.

`npm audit` reported three inherited high-severity entries through
`unplugin-vue-components@28.8.0 → chokidar@3.6.0 → braces@3.0.3`. The versions are
identical in the reference lock and the new lock. The suggested fix is a major
upgrade; it was documented, not silently applied with `audit fix --force`.
