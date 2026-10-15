# Desktop Interaction and User Journey Plan

**Goal:** Make the existing Tauri/Vue application feel like a coherent desktop workspace, reducing visual noise without hiding essential status, recovery or keyboard access.

**Authorization:** User requested research, planning and implementation, explicitly approving the decisions in advance. Subsequent request adds a user-journey audit before deciding whether more workflow steps are necessary.

## Evidence and design direction

- Windows focus visuals indicate keyboard navigation, rather than leaving a click ring on every command. Keep keyboard focus and editable-field feedback; remove pointer-only focus decoration. [Microsoft keyboard interactions](https://learn.microsoft.com/en-us/windows/apps/develop/input/keyboard-interactions).
- Prefer the installed Windows UI font, Segoe UI Variable / Segoe UI, with system fallbacks and no bundled/downloaded fonts. [Microsoft typography](https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography).
- Scrollbars must still convey position/range and remain usable by mouse and keyboard. Customize the browser-rendered rails/thumbs rather than implementing a JavaScript scrolling engine. [Microsoft scrollbar behavior](https://learn.microsoft.com/en-us/windows/win32/controls/about-scroll-bars).
- Reuse Element Plus and current monochrome tokens. Do not replace the native OS title bar, change Tauri security/window lifecycle or imitate system window buttons in HTML.

## Dependency and commit order

1. Finish preview/final integrity fixes, regression tests and Drawer QA first.
2. Implement desktop interaction styling in a separate focused commit.
3. Audit the journey on the resulting interface; apply only justified information-hierarchy/workflow changes in another commit.

## Task 1: desktop interaction foundation

**Files:** new `desktop/src/desktop.css`, existing `tokens.css`, `element-theme.css`, `main.ts`; small input-modality utility only if native `:focus-visible` cannot distinguish pointer use adequately.

- [ ] Inspect current global focus, cursor, selection and scroll rules across pages and overlays.
- [ ] Use Segoe system typography and existing compact control sizing; preserve text readability and zoom.
- [ ] Style both axes of Chromium/WebView2 scrollbars and Element Plus scrollbars with narrow neutral thumbs, transparent tracks, hover/drag feedback and stable content layout. Do not hide scrolling or replace wheel/trackpad behavior.
- [ ] Remove click-retained focus backgrounds/rings. Keep visible Tab/arrow navigation; preserve caret, text selection/copy and high-contrast system fallback.
- [ ] Prevent accidental text selection on app chrome and command controls only. Keep transcripts, descriptions, diagnostics, inputs and code selectable.
- [ ] Use desktop command cursors and restrained hover/pressed states without changing action semantics. Respect reduced motion and forced colors.
- [ ] Browser-test pointer versus keyboard focus, both scroll axes, overlays, editable fields and copyable content. Run relevant tests/type/lint/build checks.

**Accept:** no bright browser scrollbar tracks or stuck click rings; keyboard navigation remains visible; no content jumps or inaccessible overflow; no new dependencies or Rust changes.

## Task 2: user journey and information hierarchy

**Existing journey:** source/preparation → transcript → analysis/selection → cuts → preview Drawer → explicit final → human review → export.

**Decision rule:** A new step earns a main navigation destination only when it represents a distinct user decision with its own inputs, outcome and next action. Internal audio, EDL, caption and encoding stages are status details, not destinations.

- [ ] Inspect Preparation, Transcript, Analysis and Cuts at desktop/minimum sizes; identify duplicated status, always-visible technical controls and competing primary actions.
- [ ] Map each screen's user question and primary action. Treat transcript as supporting evidence, not an obligatory manual checkpoint in automatic projects.
- [ ] Keep editorial selection separate from final approval. Show preview/final availability and the next valid action without auto-generating finals or auto-approving content.
- [ ] Prefer contextual progression and collapsible technical details over adding tabs solely to split crowded screens. If a real missing decision stage remains, document the evidence before changing navigation.
- [ ] Preserve all current navigation, cancellation, resume, filters, selection, trash, review and export behaviors with regression tests.
- [ ] Save before/after QA evidence and document the final navigation decision.

**Accept:** users can identify where they are, what is required next and what is optional; no hidden recovery path, duplicate permanent players or extra mandatory clicks for automatic processing.

## Verification boundaries

Browser evidence establishes web UI behavior, not the native Tauri build. No real/private media or paid AI. Record remaining warnings, formatter baseline and untested native/high-contrast behavior explicitly.

## Execution record

- Native foundation implemented in the dedicated `style(desktop)` commit. Used
  CSS `:focus-visible` rather than an input-modality listener: browser inspection
  proved pointer commands have no outline while Tab navigation remains visible.
  Inputs retain normal selection/caret feedback. Removed the Analysis-specific
  scrollbar rules so they cannot conflict with the shared scrollbar tokens.
- Kept all four navigation destinations. Transcript is explicitly optional;
  Preparation no longer repeats the project title/metadata and now distinguishes
  new selected proposals, available previews, pending final review and approved
  export. Existing final artifacts take priority over absent historical analysis.
  No additional tabs or mandatory steps were justified by the inspected flow.
- Journey tests: four initial failures became passes; the legacy missing-analysis
  case and real preview-state contract each failed before their respective fix.
  Desktop stylesheet tests failed before the new CSS, then passed. A separate
  regression caught the conflicting per-component scrollbar and passed after
  its removal.
- Full frontend suite: 146 passed / 27 files. Focused final scrollbar/Analysis
  check: 15 passed. Type check, production build and generated API check passed.
  Lint: zero errors / 40 warnings. Format baseline: 11 untouched files fail.
- Actual browser checks: pointer/keyboard distinction, field text selection,
  preview/final playback, single player, checkbox selection without opening,
  Escape/button cleanup and focus restoration. Drawer inspected at all five
  requested sizes; Settings additionally inspected at 800×600. Viewport restored.
- Screenshots and full benchmark/compatibility notes:
  `docs/preview-final-validation.md`. Populated multi-topic analysis was covered
  by automated tests, not a new end-to-end visual fixture. OS forced-colors mode
  and native Tauri runtime remain untested.
