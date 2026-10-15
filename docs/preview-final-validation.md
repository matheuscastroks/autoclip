# Preview / Final: Implementation and Validation

## Architecture and persistence

`RenderProfile` centralizes preview (540×960, veryfast, CRF 30, AAC 96) and final
(1080×1920, medium, CRF 20, AAC 192). Both consume the same EDL, ASS captions,
title and normalized crop path. Encoder quality is not an editorial planning input.

`prepared.json` binds source bytes and metadata, analysis, candidate, EDL, captions,
font and framing artifacts. `preview.json` has independent output/hash/minimal
validation; it cannot replace `render.json`, `qa.json` or a human `review.json`.
Final QA remains the complete technical check. Export still requires valid final
bytes and the five human editorial confirmations bound to their fingerprint.

Jobs now distinguish `preview`, `render_final` and `export`. Legacy `render`
retains its earlier semantics. Final jobs consume prepared revision IDs without
constructing Whisper or an AI analyzer. Requests deduplicate active/finished
revision identities, including reordered and overlapping selections.

Revision responses expose preview availability, final state and whether final
generation is possible. TypeScript contracts are generated from Python. Preview
and final playback use existing authenticated, confined media-ticket routes.

Existing final renders are not migrated, deleted or reprocessed. Their old
custom-quality revision identity remains intact. Damaged preparation blocks new
final generation but does not hide an independently valid preview. Published
outputs can rebuild missing cache checkpoints without discarding valid bytes.

## Reproducible benchmark

Run in a new empty directory, with FFmpeg/FFprobe configured as in the runbook:

```powershell
.venv/Scripts/python.exe scripts/benchmark_video_profiles.py --output .runtime-tmp/video-benchmark-new
```

Measured on this Windows development machine, without concurrent test/build work:
30-second synthetic 1280×720 source, 24-second cut, three EDL segments, burned
title/captions, actual framing detection falling back to center crop (no face).
No transcription, remote AI or private media. One cold run and one warm run per
profile; these are observations, not a statistical/general performance guarantee.

| Measurement | Preview | Final |
| --- | ---: | ---: |
| Render and cache lookup | 6.736 s | 29.955 s |
| Technical validation | 0.145 s | 1.910 s |
| Output total | 6.881 s | 31.865 s |
| File size | 1,268,670 bytes | 7,816,965 bytes |
| Warm request, reused | 0.979 s | 0.964 s |

Shared preparation: 3.155 s, including framing 2.918 s and captions 0.007 s.
Source/fixture creation: 3.503 s. Preparation is shared, not counted twice in the
output totals. Preview output was approximately 4.63× faster in this scenario.
Real faces, long/private media and production hardware remain unbenchmarked.

A repeat on the final code produced preview 15.906 s (render/lookup 15.666 s,
validation 0.240 s) and final 96.742 s (render/lookup 93.542 s, validation 3.200 s).
Preparation was 7.059 s (framing 6.634 s, captions 0.048 s), fixture creation
6.336 s; warm reuse took 3.180 s / 2.173 s respectively. File sizes were identical.
This repeat overlapped browser QA and one short CSS regression test, so it is not
an isolated timing sample. The substantial absolute variation is why neither
run is presented as a production speed guarantee or a statistical comparison.

## Desktop and journey decisions

Keep Preparation, Transcript, Analysis and Cuts. They represent source/status,
optional evidence, proposal selection and output management respectively. Adding
tabs for internal processing stages would add mandatory navigation without a new
user decision. Preparation now suggests preview evaluation, final review or export
according to actual artifact state, including legacy outputs without analysis.
New selected proposals remain actionable when older cuts already exist.

Cuts is a flat selectable/filterable/sortable list. A right-side Element Plus
Drawer owns lazy media loading, version switching, context, details and editorial
actions. Checkbox clicks do not open it. Closing cancels stale ticket requests,
pauses/unloads the single player and restores focus. No auto-open or auto-final.

Desktop styling uses installed Segoe/system typography, neutral custom native
scrollbars, system dark controls and restrained command interaction. Pointer
focus decoration is removed from commands, not keyboard focus or editable-field
feedback. Text remains selectable outside app chrome; no JS scrolling engine,
extra UI dependencies, fake title bar or Rust/security changes were introduced.

## Evidence and limits

- Backend: 251 passed, one opt-in real-media test deselected. The Linux import
  issue was reproduced via the pytest console entry point and fixed separately;
  hosted Linux CI itself was not executed here.
- Generated TypeScript check passed. Frontend type checking and production build
  passed. Frontend: 146 tests / 27 files passed; subsequent centralized-scrollbar
  regression/analysis check: 15 passed. Lint: zero errors, 40 existing warnings.
  Global format check still fails on 11 pre-existing, untouched files; changed
  frontend files were formatted. These baseline issues were not mass-reformatted.
- Browser QA used an isolated project with synthetic FFmpeg outputs and the real
  API/job queue. Explicit final generation, cancellation, resume, completion,
  preview preservation and unchecked editorial gates were exercised.
- Drawer checked at 1920×1080, 1366×768, 1280×720, 1000×680 and 800×600: no page or
  Drawer horizontal overflow; footer visible; one player. Checkbox selection,
  lazy loading, preview/final dimensions, Escape cleanup, focus restoration and
  keyboard focus were observed. Screenshots are local ignored QA artifacts under
  `.runtime-tmp/drawer-qa-20261015/`, not committed media.
- Ticket-expiry recovery, unavailable media and stale responses have automated
  coverage; an actual hour-long browser expiration was not waited out. Native
  Tauri, OS high-contrast mode, real-face tracking and private media were not
  interactively validated. No paid provider calls were made.
