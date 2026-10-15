# Native/runtime validation — 2026-10-15

Requested after UI/UX v2 completion. Reference HEAD: `27e9b36`.
No private media or user project was modified; no real editorial approval was issued.

## Scope and safety

- Rebuild the current Tauri app, test Rust, attempt native-window inspection.
- Authenticate with existing provider credentials without logging secrets; after
  the new call authorization, run bounded real generation with synthetic text only.
- Exercise actual dependency provisioning in a new ignored QA directory, without changing application settings.
- Render synthetic video and physically export its package; verify hashes and media metadata independently.
- User subsequently authorized a new maximum of 40 calls for this validation.
  A shared persistent RequestBudget ledger caps generation; each individual probe
  was limited to one or two attempts, including repair/retry. No private text/media
  was sent, and the user's saved model/provider configuration was not changed.

## Confirmed results

### Providers: real network and credentials

`GeminiConnection.validate()` returned `status=valid`, `configured=true`, 46 models.
OpenRouter `GET /api/v1/key` returned HTTP 200 with the existing credential.
Only authentication/catalog results were retained; no key, key label, account balance
or response body was logged. No credential was replaced.

The OpenRouter metadata endpoint follows the [official API documentation](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key).
This validates real connection/authentication, not content-generation correctness.
Log: `.runtime-tmp/native-qa-providers.log`.

### Real content-generation probes (not mocked tests)

Input: 194 words of newly written synthetic Portuguese narrative about a community
library, with synthetic word timestamps/IDs. Actual adapters and isolated request
workers were used, with locally configured credentials.

| Probe | Attempts | Outcome |
| --- | --- | --- |
| Gemini `gemini-flash-lite-latest` (configured) | 1 | Complete analysis, 1 topic, 1 candidate, all 194 word IDs covered |
| OpenRouter `google/gemma-3-27b-it:free` (configured) | 1 | HTTP 404: free variant no longer available |
| OpenRouter `openrouter/free` | 2 | First response rejected by schema/ID validation; repair failed with incomplete chunked-read transport error |
| OpenRouter `google/gemma-3-27b-it` (available paid variant) | 2 | Both replies rejected; PROVIDER_INVALID_OUTPUT |
| One captured Gemma diagnostic reply | 1 | Confirmed missing topic id/label/summary, extra candidate fields in topics, non-string IDs |

**Total generation attempts: 7 / 40.** Authentication/catalog GETs are separate
metadata requests, not generation. No attempt was made to exhaust the allowance.
Available/test-model pricing was checked in the live OpenRouter catalog before
running probes. No automatic provider fallback or saved-setting change was added.

Confirmed implementation gap: Gemini sends `GeminiResponse.model_json_schema()`
to its provider; OpenRouter's actual worker sends only
`response_format={type: json_object}`. The shared prompt refers to a schema but
does not supply the topic schema. Real Gemma output therefore failed the strict
Pydantic contract. This is a failed OpenRouter analysis acceptance check, not a
credential failure or an accepted partial analysis. Fixing schema transmission/
compatibility needs regression coverage and a separate implementation change;
no production backend workaround was applied during this validation request.

Logs: `.runtime-tmp/native-qa-{gemini-generation,openrouter-generation,
openrouter-free-generation,openrouter-gemma-generation,openrouter-diagnostic}.log`.
Persistent call ledger/artifacts: `.runtime-tmp/native-qa-generation-20261015/`.

### Physical rendering/export

Command:

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest tests/integration/test_pipeline.py tests/integration/test_review_media.py -q --basetemp=.runtime-tmp/native-qa-export-20261015
```

Result: **3 passed in 75.68s**. These tests invoke real FFmpeg/ffprobe and write
real video/package files. Transcription/analysis input and editorial decisions are
explicit synthetic test fixtures, not approval of a real clip.

Independently recomputed SHA-256 and file length for all six package entries:
`clip.mp4`, `captions.ass`, `captions.srt`, `edl.json`, `metadata.json`, `words.json`.
All match `manifest.json`. ffprobe confirmed H.264 1080×1920 + AAC, 21.000s;
the MP4 is 814485 bytes. Tests also exercised rejection, unapproved export blocking,
resume/cache reuse, deleted-revision blocking, restoration and corrupted-render blocking.

Artifact root: `.runtime-tmp/native-qa-export-20261015/`.
Log: `.runtime-tmp/native-qa-export.log`.

## Native and installation checks

Windows Rust 1.99.0/MSVC Build Tools detected. The pre-existing desktop executable
was dated 2026-10-13, so it was not used as proof of the current redesign.

Initial current build and Rust test both failed because configured sidecar
`desktop/src-tauri/bin/autoclip-engine-x86_64-pc-windows-msvc.exe` did not exist.
The virtualenv lacked pip/PyInstaller. `ensurepip` and the declared desktop dependency
PyInstaller were installed into `.venv` (not the global Python) to run the existing
`scripts/build_engine_sidecar.py`. No production source/configuration workaround
was applied to hide the missing resource.

Native visual automation was attempted through the supported Computer Use runtime:
initial call, retry, then session reset/reinitialization. All window-list attempts
failed because the native pipe was unavailable (Windows error 2). No unsupported
PowerShell UI automation or alternate screen-capture helper was substituted.
Actual native visual interaction remains blocked until that service is connected.

The sidecar build subsequently passed: PyInstaller 6.22.3 produced a 188735263-byte
standalone engine. Executing its real `doctor` command passed, detecting FFmpeg,
ffprobe, configured Gemini credentials and the existing ASR model. The current
Tauri executable compiled successfully. Rust retry: **2 tests passed**, including
non-loopback and invalid-private-protocol rejection. Logs:
`native-qa-sidecar.log`, `native-qa-frozen-doctor.log`, `native-qa-rust-retry.log`.

Launched the current Tauri binary with AUTOCLIP_WORKSPACE pointing to a new empty
QA workspace, not the user's library. Verified process PID 10732, valid main window
titled AutoClip, Responding=true, one native lease, authenticated health=ok,
frontend HTTP 200 serving current `index-BkZUDfav.js`, unauthenticated config HTTP
401 and initially zero projects. This is actual native startup/session evidence,
not visual proof of playback, focus or dialogs.

Later that workspace was observed with a running prepare job not created by these probes.
The idle-only cleanup guard refused shutdown. Its app process, engine and data
were preserved; do not treat `.runtime-tmp/native-qa-desktop-20261015/` as disposable
or delete it merely because its name contains QA.

NSIS initially produced a 191139150-byte setup file, but bundler cleanup failed
with Windows sharing error 32 after the QA app had been opened. A prematurely
interrupted retry left two makensis children; only those proven-owned build PIDs
were stopped, not the active app/job. Bundle output was moved to an isolated Cargo
target for a clean repeat without locking the live executable.

An existing per-user AutoClip installation was found registered at
`%LOCALAPPDATA%\AutoClip`. A silent /D override is not a clean-machine test and can
still affect the same uninstall registration. No installer was run over it.

Provisioning uses the actual DependencyProvisioner and public FFmpeg/Whisper sources,
with base directory `.runtime-tmp/native-qa-provision-20261015/` and a 15-minute cap.
It does not alter the user's configured models/tools. Running an installer, a clean
machine, model loading and a native process/window are separate acceptance checks;
none is inferred merely from a successful download/build.

Actual fresh provisioning did **not** finish: the FFmpeg transfer reached 22413312
bytes before the 15-minute bound; cancellation was requested. That first bounded
harness left its partial QA download, not a usable installation. A separate real
Whisper-download cancellation probe passed with status=cancelled and zero .tmp
files. Existing Whisper model load/inference also passed in CPU int8 mode on the
21.014s synthetic non-speech fixture (0 segments), not a speech-quality evaluation.
Logs: `native-qa-provision.log`, `native-qa-cancel-provision.log`, `native-qa-asr.log`.

The cached-resource path also passed: valid local tools/model were physically
copied to `.runtime-tmp/native-qa-provision-cached-20261015/`. The real provisioner
reported ready with zero downloaded bytes, both copied executables ran, and the
copied Whisper model loaded on CPU. This validates reuse of already available
resources, not a successful fresh network installation.

## Final installer and remaining acceptance gates

Isolated bundle command (temporary environment only, no persistent Tauri config change):

```powershell
$env:CARGO_TARGET_DIR = '<workspace>/.runtime-tmp/native-qa-bundle-target'
npm --prefix desktop run tauri -- bundle --debug --bundles nsis
```

The already-built current main executable was copied into that target first.
Command exited **0**, finished one NSIS bundle. File:
`.runtime-tmp/native-qa-bundle-target/debug/bundle/nsis/AutoClip_0.1.0_x64-setup.exe`.
Size: **191139150 bytes / 182.28 MiB**.
SHA-256: `50fc59b92f6f6beb943e9592d9fd35cbec3610a8165b255676ea166e43ea3981`.
Authenticode: **NotSigned**. This is a local debug installer, not an optimized or
signed production release. The repeated bundler reported a bundle-type metadata
patch warning on the previously patched executable; updater behavior is not validated.
Log: `.runtime-tmp/native-qa-bundle-isolated.log`.

No Windows Sandbox executable, Hyper-V PowerShell module, VirtualBox or VMware
executable was found at the checked standard locations. No clean environment was
provided to this session. Enabling/installing virtualization was not assumed.
The existing AutoClip install and active task were left untouched. Installer
execution/upgrade was explicitly deferred pending an environment/upgrade choice.

Final status:

- Passed: current native build/startup/session, two Rust tests, frozen-engine
  diagnosis, real Gemini analysis, provider authentication, local ASR smoke,
  physical synthetic export/hash checks, cached-resource provisioning and real
  download cancellation, NSIS bundle generation.
- Failed: OpenRouter end-to-end analysis (contract violations); configured free
  model unavailable; fresh dependency download did not complete within 15 minutes.
- Not exercised: native visual interaction/playback/focus (Computer Use native
  service unavailable), clean installation/upgrade (existing install protected),
  real-content editorial approval, optimized/signed release and updater.

Only source changes: ignore generated engine sidecars/spec and record this evidence.
No backend/provider/queue/persistence/UI behavior was changed to make checks pass.
