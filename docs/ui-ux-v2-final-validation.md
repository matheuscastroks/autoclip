# UI/UX v2 — completion audit

Date: 2026-10-15. Reference: `bfaf7e5`; implementation on
`poc-openshorts-gemini`. This is frontend validation, not a native-release sign-off.
Backend, Python contracts, queue scheduling, persistence formats and Rust are unchanged.

Subsequent real-runtime checks are recorded in
[`native-runtime-validation-2026-10-15.md`](native-runtime-validation-2026-10-15.md).
They confirm native startup, Gemini generation and physical export, but expose
OpenRouter contract failures. They do not turn this browser UI audit into native
visual QA or a clean-installation sign-off.

## Product decisions and requirement coverage

| Requirement | Result / evidence |
| --- | --- |
| Consistent graphite / steel-blue desktop language | Semantic tokens and Element Plus theme; foundation controls/contrast audit and five-size screenshots. No decorative gradients/glows/glass. |
| Compact global rail / contextual header | AppRail, WorkspaceHeader, ProjectTabs; queue independent of destination, native title bar untouched. Shell navigation regression suite. |
| Four project destinations | Preparation, Transcript, Analysis, Cuts retained. Transcript is reference material, not a mandatory approval step. No internal FFmpeg steps promoted into navigation. |
| List-first library / grid / creation | Existing search/filter/sort/trash retained; legacy summaries stay unknown rather than synthesized. NewProjectDialog preserves errors/form state and prevents duplicate submit. |
| Preparation state and next action | Hero plus operational steps; technical diagnostics disclosed on demand. No invented progress. Current analysis hash now gates selected counts and generation. |
| Two-region analysis / inspection Drawer | TopicNavigation and ProposalList permanent; separate lazy ElDrawer inspector; one selection dock. Checkbox and inspection independent. |
| Hash-bound selection / discards | Eligibility, overlap, partial-analysis prohibition, selection polling and local completed-hash discards preserved. Clearing job history no longer resets unchanged editorial content. |
| Cuts / existing Drawer | Preview, final, editorial approval and export remain distinct. Five fingerprint-bound checks retained. Invalid/missing versions are never loaded or advertised as valid. |
| Supporting screens | Transcript extracted; searchable/copyable text, native timestamp buttons and cleanup. Three Settings categories preserved; paths collapsed, invalid fields revealed. Queue/onboarding use shared tokens/icons/focus lifecycle. |
| Offline icons | Static typed Fluent allowlist via unplugin-icons / @iconify-json/fluent. No remote SVG/provider. Lucide removed after migration; third-party notice updated. |
| CSS/accessibility | Keyboard focus, text selection, reduced-motion/forced-colors CSS retained. Native scroll containers themed without replacing scroll semantics. Superseded table/analysis rules removed, not overridden with more !important. |

The component names in the proposal were illustrative: existing status tags/typed
presentation and local empty states were retained instead of adding single-use
AppStatus/AppEmptyState facades. Library toolbar remains with its existing owner.
No router, API client or parallel domain-state system was introduced.

## Component inventory

Created under `desktop/src/components/`:

- `layout/`: AppRail, WorkspaceHeader, ProjectTabs.
- `library/ProjectListItem`, `dialogs/NewProjectDialog`.
- `pipeline/`: PipelineStatusHero, PipelineStepList.
- `analysis/`: TopicNavigation, ProposalList, ProposalItem,
  ProposalInspectorDrawer, SelectionDock.
- `ui/`: AppIcon (typed static icon map), TechnicalDetails.
- TranscriptPanel.

Modified: App, ProjectWorkspace, ProjectLibrary, PipelinePanel, AnalysisPanel,
ReviewPanel, ClipPreviewDrawer, SettingsPanel, GlobalQueueModal, OnboardingModal,
JobPanel, ApiKeyField, ProviderSelector and BaseModal. No component files deleted.
Supporting logic: usePipelinePresentation, useModalFocus, useProposalSelection,
useBulkSelection and revisionPresentation. Global styles/theme/tokens and generated
component declarations updated; API-generated contracts were not edited.

Definitive main tokens: canvas `#101316`, surface `#171D22`, raised `#202930`,
hover `#283540`, selected `#304451`; text `#EDF1F4` / `#A5B5BE` / `#9FB0BA`;
primary `#AFC6D5`, hover `#C5D9E6`, on-primary `#16232D`. Muted text and control
borders were raised from the initial proposal for contrast. Segoe UI Variable →
Segoe UI → system-ui; 22/16/14/13/12px scale, 34px controls, 6/8px radii.
Full definitions: `desktop/src/tokens.css`.

## Final independent review and corrections

One fresh read-only review covered `bfaf7e5..457c5e5`, source and existing backend
contracts. No Critical findings; four Important findings reproduced and fixed:

1. Preparation submitted a saved selection from an old analysis. Current completed
   hash is now authoritative for counts and emitted generation payload.
2. Removing a completed job reset unchanged selections/discards. Job-based reset
   now applies only to a genuinely new unfinished job; hash replacement still resets.
3. Drawer claimed previews existed and requested unavailable finals. Independent
   availability labels, available-only initial version, original/empty fallback and
   polling invalidation now govern loading. Existing legacy finals remain supported.
4. Discard removed the focus opener. Ordinary restoration stays with Element Plus;
   a disconnected opener falls back to the connected proposal-list region.

Also fixed both Minor findings: late hardware recommendations apply until explicit
model choice, and editing/retrying a credential clears the prior success message.
Regression logs in ignored `.runtime-tmp/`: `phase8-{drawer,selection,workflow,focus,
onboarding}-red.log`; `phase8-review-green.log` passed 60 focused tests.

Root visual audit additionally reproduced a legacy Cuts table conflict: at 1000px,
the table reached 2201px and the title 1773px because old global rules forced nowrap
and a 180px selection cell. Removing superseded globals and keeping required row
semantics scoped reduced the table to 853px; all five sizes now fit without table
horizontal overflow. This is rendered before/after evidence, not a DOM-test claim.

Additional Phase 3 coverage closes the earlier automated gap: native dialog cancel,
close/reopen, pending-create/picker cancellation guards, and automatic:false with
video tools available but ASR/credentials missing. Native dialog tests use DOM mocks;
they do not prove Tauri/Windows file-picker behavior.

## Journey matrix

| Journey | Verified UI evidence | Boundary |
| --- | --- | --- |
| First use | Onboarding diagnosis/model selection, defer, simulated install success/failure, credential pending/failure/success, final handoff | No real provisioning or OS credential write |
| Create/import | Local/URL validation, duplicate protection, recoverable form retention, import orchestration, cancel/reopen, manual preparation | Mock API/picker, not real import/download |
| Processing | Truthful phase/validation/progress; navigation and queue independence; cancel/resume/recovery event wiring | No new real engine job executed |
| Curatorship | Topic/search/filter, inspect/context bounds, overlap/eligibility, select/discard/restore, partial analysis and generation gates | No AI calls; local synthetic content |
| Review | Lazy preview/final/original, five criteria and exact hash; stale tickets, cleanup, interruption and invalid output | Synthetic playback and mocked contracts |
| Export | Only valid approved finals eligible, pending/invalid/stale approval excluded, explicit export events | No real filesystem package/export |
| Recovery | Legacy final, partial/invalid analysis, missing media/retry, job-history removal and changed analysis | Controlled fixtures; no private projects touched |
| Desktop navigation | Mouse/keyboard commands, tabs/arrows, Escape, focus return (including removed opener), text selection/internal scroll/five widths | Browser only; not native Tauri or assistive-technology certification |

Supporting suites include journey, workflow, workspace, analysis-panel,
proposal-selection/inspector, cuts-table/drawer-flow, clip-preview-drawer,
review-integration, settings-navigation, onboarding-modal/flow and global-queue.
See phase-specific validation documents for exact earlier scenarios/screenshots.

## Visual evidence

Actual Vue App/components with disposable local API fixtures and synthetic media;
all unimplemented fixture API calls reject, never fall through to real services.
Five sizes: 1920×1080, 1366×768, 1280×720, 1000×680, 800×600.
Populated/empty, processing/failure, long titles, open Drawers and support screens
are covered across the phase records. Browser QA does not validate Tauri.

Final additions under ignored `.runtime-tmp/ui-v2-qa/`:

- `phase8-long-title-table-{width}x{height}.png`: final corrected list, all states in bounds.
- `phase8-stress-{width}x{height}.png`: extremely long title and 12 expanded warnings;
  no page/Drawer horizontal overflow, footer inside viewport, internal scroll as needed.
- `phase8-media-error-800x600.png`: visible failure/retry; Escape frees navigation.
- `phase8-discard-focus.png`: keyboard discard/close; list focus and zero players.
- `phase8-ai-settings-{width}x{height}.png`,
  `phase8-duration-settings-{width}x{height}.png`: no page/panel horizontal overflow.

Closing the last proposal of a topic also restored connected list focus and released
the player. Viewport overrides were reset. Screenshots remain local, not Git media.

## Explicit review boundaries and residual risks

- Rendered geometry/control states: checked in browser and phase evidence, not
  inferred solely from tokens. OS forced-colors, actual reduced-motion mode and
  assistive technology were not exercised; supporting CSS remains in place.
- Native Tauri/dialog/focus, real provider/credential/provisioning, engine
  cancellation/resume/export and hour-long ticket expiry need release smoke tests.
  They were not replaced with paid calls or private user data for this redesign.
- Filters/scroll may reset on global destination unmount; accepted existing policy.
  Project state, completed-hash selections and background operations remain intact.
- Discards before a completed hash exists remain session-only; completing an
  analysis loads its completed-hash state. Accepted existing identity boundary:
  durable partial-job discard migration would change persistence policy, outside scope.
- Three inherited npm audit high-severity entries through the existing build-tool
  dependency chain remain documented in foundation evidence. Major upgrades are
  a separate dependency task, not an unreviewed forced audit fix.
- Seven inherited format failures and 19 lint warnings remain; no unrelated bulk
  formatting. No backend/API/persistence or media performance claims.
- Hosted CI not run (no push). Python/Rust suites not required: those layers unchanged.

## Commits by phase

| Phase | Implementation / evidence |
| --- | --- |
| 0 | `992718e` baseline and acceptance ledger |
| 1 | `4add758`, `db49719`, `9b487dd` tokens/Fluent/validation |
| 2 | `eeb2eb5`, `882af72`, `504afdd` shell/navigation |
| 3 | `80340f3`, `80348a3`, `0cb97f6` library/dialog |
| 4 | `cbf4aae`, `c14fc79` Preparation |
| 5 | `750efa5`, `db04f69` editorial Analysis |
| 6 | `c1b2321`, `dd0713a` Cuts/review |
| 7 | `ff80a4c`, `185f223`, `7077d9c`, `14bc982`, `7f5e768`, `6d998f3`, `457c5e5` support screens, cleanup, setup and notices |
| 8 | `4e026d6`, `20d8a18`, `1f83e67`, `0bdfeab`, `a57686b` review corrections and coverage; `5e94c77` long-title table CSS correction |

## Final gates

Post-CSS final verification (local, 2026-10-15):

| Command | Result |
| --- | --- |
| `npm --prefix desktop run check` | Passed |
| `npm --prefix desktop run lint` | 0 errors / 19 inherited warnings |
| `npm --prefix desktop run format:check` | Failed on the same seven inherited files, no modified file failing |
| `npm --prefix desktop run test:run` | 243 passed / 39 files; exit 0 |
| `npm --prefix desktop run build` | Passed; 1742 modules; JS 461.38 kB / gzip 154.98; CSS 484.64 kB / gzip 69.73 |
| `git diff --check` | Passed |

Logs: `.runtime-tmp/phase8-final-full.log` and
`.runtime-tmp/phase8-verified-{check,lint,format,build}.log`. The final full run
started at 17:10:11 and finished in 365.03s under concurrent local activity;
this is test-run evidence, not an application performance benchmark.

Inherited Prettier files: `src/api/client.ts`, `src/components/JobQueueItem.vue`,
`src/composables/useJobQueue.ts`, `src/composables/usePipelineSteps.ts`,
`src/composables/usePolling.ts`, `tests/app-toast.test.ts`,
`tests/openrouter-settings.test.ts` (all relative to `desktop/`).

Phase 8 acceptance is complete for this frontend delivery, with the explicit
native/external release-validation limits above. No push, merge or hosted CI
success is implied. The linked secondary worktree was preserved throughout.
