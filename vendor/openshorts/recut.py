"""
Recut engine for the clip editor: a per-clip EDL (list of source segments) is
turned into a rendered clip.

The pure helpers here are standard-library only (plus ffmpeg_utils, which is
also light) so the module imports in the thin CI environment; everything heavy
(reframing, watermark, auto-captions live in main.py) is imported lazily and
only on the paths that need it.

Two render paths:

- FAST: every segment falls inside the range the canonical clip was originally
  cut from, so the recut can be cut straight out of the already-reframed
  canonical file. No ML, no source video needed, seconds instead of minutes.
- SOURCE: at least one segment reaches outside that range (or there is no
  canonical file), so the recut is cut from the source video and re-reframed
  with the same engine the pipeline used.
"""

import json
import os
import shutil
import subprocess
import time
import uuid

from .ffmpeg_utils import (METADATA_SCRUB, QUALITY_FAST, audio_encode_args,
                          video_encode_args)

# EDL limits. Deliberately generous — the editor is for humans fixing cuts,
# not for stitching feature films.
MAX_SEGMENTS = 12
MIN_SEGMENT_SECONDS = 0.5
MAX_TOTAL_SECONDS = 180.0

# Segments may start/end a hair outside the canonical range through float
# round-tripping; treat them as inside.
RANGE_TOLERANCE = 0.05


class RecutError(ValueError):
    """Invalid EDL — safe to surface verbatim as a 400 detail."""


def normalize_segments(segments, source_duration=None, *, max_total_seconds=MAX_TOTAL_SECONDS):
    """Validate and clamp an EDL. Returns [{'start': float, 'end': float}, ...].

    Order is preserved — the segment order IS the clip order, and reusing a
    source range twice is legal (an echo/replay is a real editing move).
    """
    if not isinstance(segments, (list, tuple)) or not segments:
        raise RecutError("segments must be a non-empty list")
    if len(segments) > MAX_SEGMENTS:
        raise RecutError(f"too many segments (max {MAX_SEGMENTS})")

    normalized = []
    for i, seg in enumerate(segments):
        try:
            start = float(seg["start"])
            end = float(seg["end"])
        except (KeyError, TypeError, ValueError):
            raise RecutError(f"segment {i + 1}: start/end must be numbers")
        if start != start or end != end:  # NaN guard
            raise RecutError(f"segment {i + 1}: start/end must be numbers")
        start = max(0.0, start)
        if source_duration is not None:
            end = min(float(source_duration), end)
            start = min(start, float(source_duration))
        if end - start < MIN_SEGMENT_SECONDS:
            raise RecutError(
                f"segment {i + 1} is shorter than {MIN_SEGMENT_SECONDS}s")
        normalized.append({"start": round(start, 3), "end": round(end, 3)})

    if total_duration(normalized) > max_total_seconds:
        raise RecutError(f"clip would exceed {max_total_seconds:.0f}s")
    return normalized


def total_duration(segments):
    return round(sum(s["end"] - s["start"] for s in segments), 3)


def within_range(segments, range_start, range_end, tolerance=RANGE_TOLERANCE):
    """True when every segment fits inside [range_start, range_end]."""
    return all(
        s["start"] >= float(range_start) - tolerance
        and s["end"] <= float(range_end) + tolerance
        for s in segments
    )


def rebase_segments(segments, range_start, range_end=None):
    """Map source-absolute segments onto a file cut at ``range_start``.

    Used by the fast path: the canonical clip's t=0 is the source's
    ``range_start``. Clamps to the file bounds so tolerance-admitted segments
    never produce negative seek times.
    """
    rebased = []
    for seg in segments:
        start = max(0.0, seg["start"] - float(range_start))
        end = seg["end"] - float(range_start)
        if range_end is not None:
            end = min(end, float(range_end) - float(range_start))
        rebased.append({"start": round(start, 3), "end": round(end, 3)})
    return rebased


def snap_segments(segments, transcript, source_duration):
    """Snap each segment's bounds onto word boundaries (ground truth beats
    millisecond arithmetic — same rationale as the pipeline's snapping)."""
    from .clip_selection import snap_clip_to_words

    words = transcript_words(transcript)
    if not words:
        return segments
    snapped = []
    for seg in segments:
        start, end = snap_clip_to_words(
            seg["start"], seg["end"], words, source_duration,
            min_duration=MIN_SEGMENT_SECONDS, max_duration=MAX_TOTAL_SECONDS)
        snapped.append({"start": start, "end": end})
    return snapped


def transcript_words(transcript):
    """Flatten a Whisper transcript to [{'w','s','e'}, ...] sorted by start."""
    words = []
    for segment in (transcript or {}).get("segments", []):
        for w in segment.get("words", []) or []:
            try:
                words.append({
                    "w": str(w.get("word", "")).strip(),
                    "s": float(w["start"]),
                    "e": float(w["end"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
    words.sort(key=lambda w: w["s"])
    return words


def virtual_transcript(transcript, segments):
    """Remap a source-absolute transcript onto the concatenated clip timeline.

    Each EDL segment becomes one synthetic transcript segment whose words are
    shifted so t=0 is the start of the recut clip. This is what lets
    auto-captions and subtitle restyles work on multi-segment clips: they keep
    slicing "words between clip_start and clip_end" exactly as before, against
    this transcript with clip_start=0.
    """
    out_segments = []
    offset = 0.0
    for seg in segments:
        seg_start, seg_end = float(seg["start"]), float(seg["end"])
        seg_duration = seg_end - seg_start
        words = []
        for w in transcript_words(transcript):
            if w["e"] <= seg_start or w["s"] >= seg_end:
                continue
            words.append({
                # Leading space = Whisper's word-boundary convention.
                # transcript_words() strips it, and without it the caption
                # block collector treats every word as a continuation fragment
                # and burns the whole line glued together.
                "word": " " + w["w"],
                "start": round(max(0.0, w["s"] - seg_start) + offset, 3),
                "end": round(min(seg_duration, w["e"] - seg_start) + offset, 3),
            })
        out_segments.append({
            "start": round(offset, 3),
            "end": round(offset + seg_duration, 3),
            "text": "".join(w["word"] for w in words).strip(),
            "words": words,
        })
        offset += seg_duration
    return {
        "language": (transcript or {}).get("language", "en"),
        "segments": out_segments,
    }

