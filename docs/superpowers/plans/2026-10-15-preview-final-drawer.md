# Quick Preview, Final Render and Drawer Implementation Plan

> **For agentic workers:** Use `executing-plans` to implement this plan task-by-task in the current worktree. Do not delegate edits to overlapping files.

**Goal:** Evaluate a lightweight preview before explicitly rendering, reviewing and exporting a final clip.

**Architecture:** Keep editorial preparation shared and immutable across output profiles. Store lightweight previews separately from final render/QA artifacts; retain the existing human, hash-bound final approval gate. Expose both versions through the current authenticated media tickets and one on-demand Element Plus Drawer.

**Tech Stack:** Python 3.12, Pydantic, FFmpeg/libass, FastAPI/SQLite jobs, Vue 3/TypeScript, Element Plus, Vitest.

**Spec:** User-supplied “AutoClip — Plano de implementação: prévia rápida, renderização final e visualização em Drawer”, sections 0–12, 2026-10-15.

## Baseline and constraints

- HEAD: `2ff41d3e284bba5c9adf56d78be7aca1257de2e9`; clean worktree. Only Settings UI differs from reference `e1f7086`.
- No other session agents; layout worktree is clean. Recheck status before each commit.
- CI collection failure reproduced using `.venv/Scripts/pytest.exe tests/api/test_response_contracts.py --collect-only`: `ModuleNotFoundError: scripts`. Fix separately.
- Preview: 540×960, 30 FPS, H.264/veryfast/CRF 30, AAC 96k. Final: 1080×1920, 30 FPS, H.264/medium/CRF 20, AAC 192k.
- Same timestamps, pauses, EDL, captions, title and normalized face path for both profiles. No remote AI calls in tests.
- Preserve legacy `render` as full-quality rendering. Existing final artifacts require no migration or automatic reprocessing.
- Preview manifests must never overwrite `render.json`, `qa.json` or editorial decisions. Final rendering requires an explicit request.
- Preserve atomic publication, cache/file hashes, cancellation, per-project queue serialization, resumability, trash and approval/export gates.
- No new UI libraries, public encoder controls, Rust changes or unrelated reformatting.

## Review focus

1. Changed or corrupt shared files must reject final rendering without destroying a valid preview.
2. Preview/final requests for different clips must not be incorrectly deduplicated.
3. Old finals with no lightweight preview must remain reviewable, playable and exportable.
4. Rapid Drawer selection/closing must not attach a stale ticket or leave a hidden player running.
5. Changing output quality alone must not rerun Whisper, AI, EDL planning, captions or face detection.

## Delivery 0: isolated CI collection repair

Result: `b05bd0e`; console-entry contract suite: 5 passed. Linux CI has not been run locally.

**Files:** `pyproject.toml`, `tests/api/test_response_contracts.py` (existing regression).

- [x] Reproduce failure through the pytest console entry point.
- [ ] Add an explicit pytest repository import path; do not change product packaging for a test helper.
- [ ] Run console-entry collection and contract tests, then commit `fix(ci): ...` separately.

## Delivery 1: profiles and renderer

Result: `ada761a`; focused render/crop tests: 15 passed; synthetic profile parity: 1 passed; backend suite: 239 passed, 1 real-media deselected.

**Files:** `engine/contracts/models.py`, `engine/render/ffmpeg.py`, `engine/render/verify.py`, `engine/media/face_tracking.py`, new `tests/unit/test_render_profiles.py`, synthetic integration tests.

**Interfaces:** typed `RenderProfile`; centralized preview/final constants; compatible `ExportConfig` defaults; `crop_expression(points, width=1080)`; full QA remains final-only.

- [ ] Add failing profile/command/crop-parity tests, including legacy defaults.
- [ ] Parameterize scale, crop, FPS, preset, CRF and audio bitrate. Keep ASS design coordinates unchanged so libass scales both outputs proportionally.
- [ ] Render one synthetic multisegment cut in both profiles; assert dimensions, duration, A/V streams and equivalent face positioning.
- [ ] Run focused tests and review/commit this delivery.

## Delivery 2: preparation and persistent outputs

Result: preview/final persistence and cache integration: 4 passed; review/export and precomputed-analysis regressions: 8 passed. Encoder quality is excluded from presentation revision identity; old revisions remain indexed and untouched.

**Files:** `engine/pipeline/runner.py`, new `engine/pipeline/outputs.py`, contracts and cache/integration tests.

**Interfaces:** `run_project(..., stop_after='preview')`; `render_final(project_root, revision_ids, ..., cancelled, progress)` consumes validated prepared revisions, not ASR/AI. A `preview.json` manifest stores its own render, profile, minimal validation and shared fingerprint. `prepared.json` binds source, analysis, candidate, EDL, captions and crop.

- [ ] Pin failing tests for shared artifact reuse, content identity, corrupt input, cancellation and final failure preservation.
- [ ] Separate editorial EDL cache identity from presentation identity. Presentation revisions may differ for changed content/style, but never for output profile alone.
- [ ] Publish previews independently; write final render/QA only after explicit final rendering. Full final QA and editorial approval remain separate.
- [ ] Verify repeated requests/restart reuse, final failure, legacy exports and no ASR/AI calls; review and commit.

## Delivery 3: API, jobs and media

**Files:** `engine/contracts/api.py`, `engine/api/{jobs,job_worker,reviews,app,media}.py`, generated `desktop/src/generated/api.ts`, API tests.

**Interfaces:** jobs `preview`, `render_final`, legacy `render`, `export`; final requests identify prepared revision IDs. Revision responses include separate preview/final availability. Media assets identify the revision and version, never an arbitrary path.

- [ ] Add failing API/queue tests for typed responses, per-output deduplication, cancellation/resume, deletion and ticket/path protections.
- [ ] Reuse existing scheduling and progress; final operations never construct an AI analyzer. Restore each operation with its original identity.
- [ ] List lightweight and legacy/final versions without interpreting preview validity as final QA or editorial approval.
- [ ] Generate TypeScript with `python scripts/generate_api_types.py`; verify `--check`, API tests and commit.

## Delivery 4: Drawer and Cuts

**Files:** new `desktop/src/components/ClipPreviewDrawer.vue`, `ReviewPanel.vue`, `ProjectWorkspace.vue`, `App.vue`, API/domain/composable files where needed, focused Vitest tests.

**Interfaces:** one `v-model` ElDrawer (`direction="rtl"`, responsive size, destroy-on-close), lazy version-specific media loader, render-final/cancel/review/export events.

- [ ] Add tests for row versus checkbox clicks, selection retention, close/Escape, stale loads, version switching and media retry.
- [ ] Remove permanent review player. Keep list filtering, sorting, bulk selection, trash and existing export operations.
- [ ] Put player/details/checklist in Drawer; retain five required human confirmations and reset them when final fingerprint changes.
- [ ] Gate final generation, review and downloads by their actual output/job state. Do not auto-open Drawer on job completion.
- [ ] Run targeted Vitest/type checks, inspect desktop/compact layouts, review and commit.

## Delivery 5: integration, benchmark and final verification

**Files:** analysis action/copy, new reproducible synthetic benchmark script and results documentation, final regression coverage.

- [ ] Change Analysis generation to `preview` and “Gerar prévias rápidas”; update polling/progress labels for both operations.
- [ ] Benchmark preparation, face/caption work, preview/final rendering, validation, file sizes and warm-cache reuse with a synthetic source. Record source/cut duration and EDL segment count. Never infer speedups without measured results.
- [ ] Execute backend suite, generated-type check, frontend check/lint/format/test/build. Report pre-existing failures separately, without unrelated formatting changes.
- [ ] Browser QA at 1920×1080, 1366×768, 1280×720, 1000×680 and 800×600 where supported; long titles, warnings, absent media and scrolling. Save screenshots.
- [ ] Document legacy compatibility, verification evidence and untested native/real-media behavior. Commit focused integration/benchmark changes; confirm final worktree state.
