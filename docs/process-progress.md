# Processing progress

## What the interface reports

Preparation, task queues, clip generation, final-render drawer and dependency
installation share a progress presentation. It distinguishes a measured stage
percentage from an explicitly estimated overall percentage. A finished encoding
step is not a validated final, an editorial approval, or a completed export.

Known totals use bytes, media time, validated analysis windows or processing
samples. Unknown download sizes show bytes transferred rather than a fictitious
zero. Model initialization and a pending provider response remain indeterminate.
The existing provider timeouts, retry limits and editorial gates are unchanged.

Stage ETA needs at least three advancing observations spanning ten seconds.
Overall forecasts require at least three compatible successful samples for every
planned phase. The local history retains the last 20 samples per configuration,
up to 100 configurations. Matching considers operation, hardware, model/provider,
analysis settings, duration bucket and selected output workload. Batches weight
clips by their selected duration rather than treating the first clip as the batch.
No transcript, credential or source path is stored in the history.

## Liveness and failures

The CLI writes a minimal startup marker before media/provider imports and a
heartbeat every five seconds. Heartbeat is not measured advancement. The API
reports initialization unconfirmed after 30 seconds, missing heartbeat after
30 seconds, and no advancement after 120 seconds. These are diagnostic warnings,
not declarations of a hang and not automatic cancellation/restart instructions.

An operation reaches overall 100% only after its successful result is persisted.
Failures and cancellations keep the last measured stage value and clear ETA.
Older workers and projects remain readable. Legacy render-time counters are
interpreted only when a newer telemetry snapshot is absent, avoiding reuse of
stale encoding counters during validation.

## Local persistence and compatibility

- Job-local `startup.json`: process initialization and heartbeat, no payload.
- Job-local `telemetry.json`: current numeric observation, atomic and throttled.
- Workspace `.autoclip/progress-history.sqlite`: bounded duration calibration.
- Existing `progress.json`, manifests, media artifacts and review files remain.

Media fingerprints exclude progress values. An exact allowlist maps the four
reviewed telemetry-only source changes to their prior runtime hashes; unknown
source changes use their actual hashes. No artifact is migrated or reprocessed
automatically. Dependency extraction stages files separately and publishes only
completed tools, preserving installed executables when cancellation occurs.

## Reproducible offline checks

Use unique temporary directories when running pytest concurrently; the repository
default `.pytest_temp` is shared between invocations.

```powershell
.venv/Scripts/python.exe -m pytest -m "not real_media" -q --basetemp=.runtime-tmp/progress-full
.venv/Scripts/python.exe scripts/generate_api_types.py --check
npm --prefix desktop run test:run -- --pool=threads --maxWorkers=1
npm --prefix desktop run check
npm --prefix desktop run lint
npm --prefix desktop run format:check
npm --prefix desktop run build
```

After building the sidecar, the following creates a fresh scratch workspace,
generates four seconds of silent video, imports it and optionally exercises local
Whisper. Silence must fail transcription, not masquerade as a successful project.
The helper never starts an analysis or makes remote AI calls.

```powershell
.venv/Scripts/python.exe scripts/validate_progress_runtime.py --engine desktop/src-tauri/bin/autoclip-engine.exe --asr-model research/models/whisper-small
```

Run `npm --prefix desktop run dev` and open `/tests/fixtures/progress.html` for a
synthetic visual fixture. It does not access APIs or modify projects.

## Known limitation

The original native worker that remained open without startup/progress output
was not restarted or cancelled. Its wait did not reproduce with a fresh standalone
probe; its cause remains unconfirmed. New telemetry cannot retrofit that running
binary. Deploy/restart the updated app only at a safe point, preserving active jobs.

## Validation on Windows, 2026-10-15

- Backend: 274 passed, one opt-in real-media test deselected. Includes generated
  video, real FFmpeg audio/render/verification and physical fixture export.
- Frontend: 248 passed across 40 files; type-check, generated types and build passed.
- ESLint: zero errors and 19 inherited warnings. Format check still reports six
  untouched files: `client.ts`, `useJobQueue.ts`, `usePipelineSteps.ts`,
  `usePolling.ts`, `app-toast.test.ts` and `openrouter-settings.test.ts`.
- Independent review findings were covered with failing regressions and fixed.
- Synthetic browser fixture inspected, including unknown totals and inactivity;
  this is not a full-window or native Tauri visual-validation matrix.
- No paid provider calls, real private media, installer upgrade or live-job restart.
