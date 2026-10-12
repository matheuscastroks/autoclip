# Execution ledger — docs/superpowers/plans/2026-10-12-poc-openshorts-gemini.md

Architecture and native execution plan approved by user on 2026-10-12.

Ruling: this workspace is projectless Git-wise; execute in the named project directory without initializing Git or creating a worktree. Native worktree/scripts require a repository; preserve this ledger and test reports instead. No commits or pushes are implied.

Pre-flight: contracts (task 1) feed source/ASR/analysis/EDL/render/runner (tasks 2–7); shared schema_version 1.0 and integer microseconds. ArtifactRef and PipelineConfig are defined with the contracts to avoid later interface drift.
Pre-flight: analysis completeness and candidate schema (task 4) feed review/EDL (task 5); missing window results are failures, not complete empty lists.
Pre-flight: render outputs (task 6) feed manifests/export (task 7); preview never implies human approval.
Ruling: task 8 real Gemini requests need a locally configured secret. Complete deterministic engine/test work and a clearly marked manual preview first; record remote analysis and human editorial acceptance as pending until provided, without fabricating selections.

Task 1: complete (contracts 3/3; editable package installed; schemas and product lock generated). Git foundation commit ecf326d.

Task 1: contracts/boundary tests RED (3 missing-engine failures) -> GREEN (3/3); 12 schemas generated; package installed editable into isolated .venv. Product dependency freeze recorded.
Task 2: media tests RED (5 missing-module failures) -> GREEN (5/5); real FFmpeg WAV/probe exercised with Unicode/apostrophe fixture.
Task 3: adapter tests RED (3 missing-module failures) -> GREEN (3/3); full-source real CPU transcription running separately.
Task 4: tests RED (10 missing-module failures) -> GREEN (10/10). A failing fixture mutated start before end; corrected fixture order, not contract validation. Gemini actual requests remain pending local credential.
Task 5: tests RED (5 missing-module failures) -> GREEN (5/5); protected EDL, review and captions exercised.
Task 6: command tests RED (2 missing-module failures) -> GREEN (2/2); actual render integration in progress.

Task 6: real integration passed after diagnosing removed FFmpeg9 filter_complex_script and updating fixture rotation with display_rotation. Actual decode, dimension/codec/FPS, source offset, caption frame and non-silent audio checks passed.
Task 7: tests RED (6 missing-module failures) -> GREEN (cache/cancel/CLI tests); complete injected pipeline with actual FFmpeg passed, including resume reuse and review-gated export. ReviewDecision now binds a content fingerprint; regression tests observed RED -> GREEN for stale caption/review binding.
Ruling: export directories use the first 16 hash characters for Windows path length, preserving/checking the full package hash in manifest. Collision raises EXPORT_CONFLICT instead of overwriting. Cost if wrong: longer names would require Windows long-path handling.
Ruling: this repository's original code uses MIT to match the permitted OpenShorts core; vendor copyright preserved, FFmpeg/models/fonts remain external and unbundled. Public packaging audit remains a release gate.
Task 8: real manual 25s render technical QA passed; selection clearly labeled manual and editorial approval absent. Full source CPU ASR running; Gemini key not yet configured according to doctor.

Ruling update: user explicitly requested Git creation. Initialize a local repository on poc-openshorts-gemini and commit verified stages; do not create a remote or push without instructions. This supersedes the earlier no-initialization ruling.

Final independent review: eight findings, one fix pass, no second review dispatched. VFR picture clock now follows EDL start; cache includes vendor/model auxiliary assets/tool/font/dependency identities; remote policy is excluded from semantic cache keys; numeric digital silence fails QA; response arrays are required; real HTTP transport errors and capped Retry-After are handled; cancellation reaches extraction, provider subprocess and QA; all model assets are required with local_files_only. Nine regression tests observed RED then GREEN; targeted suite 42 passed. Previously full suite 49 passed/1 skipped; final post-live fixes result is recorded in poc-results/tests.xml.

Task 8: complete-source CPU/int8 ASR finished: 5,414 words in 2,841.406 seconds. Original source/hash preserved. Manual 25.67-second fit-blur/caption preview passed technical QA; human editorial acceptance is absent.

Live request diagnosis: three early HTTP400 attempts rejected additional_properties in response_schema. Fixed to response_json_schema following Google structured-output documentation; wire regression RED -> GREEN. A subsequent small-window run was interrupted because full coverage required 22 windows. Exact attempts of that interrupted run cannot be recovered; reserve its entire 16-call cap, plus three prior attempts = 19 conservatively. Only ONE further request is permitted under this authorization, including retries; no subsequent remote rerun without a new budget. Local instrumentation retains sanitized error metadata only.

Ruling: add bounded configurable window duration/text size and budget preflight. For this 29-minute source use one 1,800-second / 300,000-character window, preserving full transcript coverage and global argument context; candidates still require 20–60 seconds and human review. Default smaller windows remain available. Window settings belong to semantic cache identity. Two budget/window regressions observed RED -> GREEN. Risks: broader windows may alter selection; no claim of superior editorial quality without human review.

Ruling: reuse the already completed 47-minute ASR with a source/hash-validated injected adapter and explicit restoration provenance/cache identity. Do not seed the default ASR worker cache as if current code executed that inference.

Deferred minor/phase findings: review UI status after resume; clean-machine installer validation; CLI caption/manual-selection editing; concurrency locks/SQLite/API/desktop UI; tracking and pause removal; human WER/timing/editorial rubric; redistribution audit. Existing approval binding, Unicode argv, vendor attribution and text-only boundaries were accepted by reviewer. A PNG smoke proves rendering only; sparse-VFR regression additionally compares actual image frames. These limits do not become automatic editorial approval.

Final observed result: 52 passed, 1 skipped in 71.92 seconds. One complete-source Gemini request returned HTTP504 timeout; its retry was refused by the one-call budget. Remote authorization conservative upper bound = 20 exhausted; actual interrupted-run count is unknown, not claimed as exactly 20. Selection real and human acceptance remain pending; no fabricated semantic outputs. No further API requests made. Task 8 is partially validated, not complete.

Ruling: preserve the requested local Git branch and commits. There is no separate base branch or remote to integrate; do not infer publication/merge authorization. This applies the user's explicit local Git request to branch finishing.
