# Process progress implementation ledger

Approved design: measured stage percentages, estimated overall completion when
supported by observations, and explicit initialization/inactivity feedback.

## Constraints

- Work in the current checkout; preserve the running native application and jobs.
- No paid AI calls, transcript changes, automatic approvals, or destructive migration.
- Keep progress outside media fingerprints; adopt legacy caches only for exact,
  reviewed telemetry-only changes, with regression coverage.
- Existing jobs and clients remain readable; regenerate TypeScript contracts.

## Tasks

- [x] 1a. Add early startup/heartbeat observability.
- [ ] 1b. Confirm the original frozen-worker wait cause; fix only if reproduced.
- [ ] 2. Add compatible progress contracts, collection and estimation.
- [ ] 3. Instrument preparation, analysis, rendering, verification, export and provisioning.
- [ ] 4. Share progress presentation across preparation, queues, drawer and onboarding.
- [ ] 5. Run regression suites, isolated runtime smoke and independent review.

## Verification record

- Baseline: `pytest tests/unit/test_progress.py tests/api/test_jobs.py tests/api/test_response_contracts.py -q`: 14 passed.
- Pre-flight: stage counters feed a single compatible API contract; frontend consumes generated types.
- Ruling: use the current checkout with isolated fixtures, per the user's explicit selection.
- Initial diagnosis: the existing native worker has no progress file, an empty log,
  and unchanged CPU usage. Cause not yet proven; never equate PID existence with progress.
- Startup probe: a fresh copy of the existing sidecar exited with the expected
  failure on an isolated invalid request. The original wait did not reproduce.
- Task 1a: `test_job_startup` failed on the missing marker, then passed; startup,
  progress and jobs subset: 10 passed. Heartbeat contains no user payload.
- Ruling: do not guess at a PyInstaller fix or restart the existing job; retain
  the unresolved native wait as an explicit validation limitation.
