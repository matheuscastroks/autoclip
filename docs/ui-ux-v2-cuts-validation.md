# UI/UX v2 — Cuts refinement validation

## Scope and decisions

Phase 6, based on `db04f69`. Existing table, filters, bulk selection, media tickets,
Drawer, final-render request, cancellation/resume, deletion and five editorial
criteria were preserved. No backend or persistence changes.

The final column now distinguishes file availability from editorial status rather
than using approval as its final-render label. Interrupted/cancelled final work
cannot continue to look actively rendering. A valid preview remains available.
Secondary cut details start collapsed; header duration/status, player and review
criteria remain immediately available. Existing publication/warning disclosures,
original playback and media recovery are unchanged.

`desktop/src/domain/revisionPresentation.ts` centralizes final availability and
export eligibility for ReviewPanel, ClipPreviewDrawer, bulk selection and Preparation.
Ruling: explicit `invalid`/`not_generated` final state overrides an old technical
pass/approval combination; omitted legacy `final_state` retains its prior meaning.
Cost: inconsistent stale responses disable export until valid current data arrives;
benefit: preview, technical and human approval states cannot be conflated visually.
The backend remains authoritative and independently validates export.

## Verification

New RED→GREEN regressions reproduced invalidated-final export controls, technical
failure with old approval in the Drawer, and interrupted work labeled rendering.
Existing row/checkbox, filters, review fingerprints, five criteria, stale media,
retry, cleanup, explicit final request and failure-path tests ran unchanged.

- `npm --prefix desktop run test:run`: **209 passed / 36 files**.
- `npm --prefix desktop run check`: passed on final rerun.
- `npm --prefix desktop run lint`: **0 errors / 29 inherited warnings**.
- `npm --prefix desktop run format:check`: same **9 inherited failing files**.
- `npm --prefix desktop run build`: passed; JS **465.62 kB / gzip 157.29**,
  CSS **489.54 kB / gzip 70.74**.
- `git diff --check`: passed.

An intermediate type-check failure from removing a still-used type import was
corrected before the final rerun; it is not counted as a passing command.

## Browser QA and limits

Actual App with disposable local fixtures and synthetic media, not private media.
Cuts and final Drawer inspected at 1920×1080, 1366×768, 1280×720, 1000×680 and
800×600: no measured horizontal page/Drawer overflow; footer within viewport,
single player, details closed. A fresh stable 1366×768 inspection confirmed five
unchecked criteria after switching to Final. The interrupted-final fixture at
800×600 showed `Final interrompida`, playable preview and explicit resume, with
no editorial approval/export. Existing real request behavior is covered by tests,
not represented as a new real render/cancellation/export run here.

Screenshots: ignored `.runtime-tmp/ui-v2-qa/phase6-cuts-<size>.png`,
`phase6-final-drawer-<size>.png` and `phase6-interrupted-drawer-800x600.png`.
Browser QA does not validate native Tauri. No hosted CI, real video processing,
paid AI or Python/Rust suite was executed for this frontend-only refinement.
Final cross-phase review/audit remains part of Phase 8.
