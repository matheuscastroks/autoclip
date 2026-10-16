import json
import subprocess
import time
from pathlib import Path
from uuid import uuid4
import pytest

from engine.contracts import (
    Span, EDLArtifact, CropArtifact, CaptionArtifact, ExportConfig,
    Source, RenderArtifact, PREVIEW_PROFILE, FINAL_PROFILE
)
from engine.media.probe import probe_source
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.presets import get_preset, VIDEO_STYLE_PRESETS
from engine.render.verify import verify_render, verify_preview
from engine.render.opening import add_opening
from vendor.openshorts.subtitles import generate_ass_from_captions


def _generate_synthetic_video(ffmpeg, path: Path, duration_sec: float = 3.0):
    cmd = [
        str(ffmpeg), '-v', 'error', '-y',
        '-f', 'lavfi', '-i', f'testsrc2=size=320x180:rate=25:duration={duration_sec}',
        '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration_sec}',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k',
        str(path)
    ]
    subprocess.run(cmd, check=True)


def test_four_presets_generate_distinct_ass_and_render(tmp_path, ffmpeg, ffprobe):
    """Verifies that all 4 presets generate valid ASS, distinct styling, and render via FFmpeg."""
    work = tmp_path / 'presets_test'
    work.mkdir()
    source_file = work / 'source.mp4'
    _generate_synthetic_video(ffmpeg, source_file, duration_sec=3.0)
    source_raw = Source(local_path=source_file, sha256='0'*64, duration_us=3_000_000)
    source = probe_source(source_raw, ffprobe)

    duration_us = 3_000_000
    edl = EDLArtifact(
        source_id=source.id,
        transcript_id=uuid4(),
        spans=[Span(source_start_us=0, source_end_us=duration_us, output_start_us=0, output_end_us=duration_us)],
        duration_us=duration_us,
        protected_word_ids=[],
    )

    rendered_files = {}
    ass_files = {}
    benchmarks = {}

    words_payload = [
        {'text': 'Primeira', 'startMs': 200, 'endMs': 600},
        {'text': 'palavra', 'startMs': 600, 'endMs': 1000},
        {'text': 'chave', 'startMs': 1000, 'endMs': 1400},
        {'text': 'demonstrativa', 'startMs': 1500, 'endMs': 2500},
    ]

    for preset_id in ['karaoke_yellow', 'editorial_sober', 'documentary', 'impact']:
        preset = get_preset(preset_id)
        spec = preset.caption
        ass_path = work / f'sub_{preset_id}.ass'
        srt_path = work / f'sub_{preset_id}.srt'
        generate_ass_from_captions(
            words_payload,
            str(ass_path),
            max_chars=spec.max_chars,
            max_duration=spec.max_duration,
            alignment=spec.alignment,
            fontsize=spec.fontsize,
            font_name=spec.font_name,
            font_color=spec.font_color,
            border_color=spec.border_color,
            border_width=spec.border_width,
            highlight_color=spec.highlight_color,
            bg_color=spec.bg_color,
            bg_opacity=spec.bg_opacity,
            effect=spec.effect,
            uppercase=spec.uppercase,
            margin_v=spec.margin_v,
            letter_spacing=spec.letter_spacing,
            max_words=spec.max_words,
            mode=spec.mode,
            bold=spec.bold,
            shadow=spec.shadow,
            fade_ms=spec.fade_ms,
            accent_prefix=spec.accent_prefix,
        )
        srt_path.write_text('1\n00:00:00,200 --> 00:00:01,200\nPrimeira palavra\n\n')
        ass_content = ass_path.read_text(encoding='utf-8')
        ass_files[preset_id] = ass_content

        # Confirm preset-specific ASS styles
        if preset_id == 'karaoke_yellow':
            assert '&H00CCFF&' in ass_content or '&H00D7FF' in ass_content
        elif preset_id == 'editorial_sober':
            assert preset.caption.font_name in ass_content
        elif preset_id == 'documentary':
            assert '&H1F281E14' in ass_content or '&HA8784A&' in ass_content
        elif preset_id == 'impact':
            assert '&H006B6BFF' in ass_content or '&H00504EFA' in ass_content or 'fscx' in ass_content or 't(' in ass_content

        caps = CaptionArtifact(
            transcript_id=edl.transcript_id,
            edl_revision_id=edl.revision_id,
            revision_id=uuid4(),
            style_id=preset_id,
            words=[],
            ass_path=ass_path,
            srt_path=srt_path,
            font='Arial',
        )

        out_dir = work / f'out_{preset_id}'
        renderer = FFmpegRenderer(ffmpeg)
        t0 = time.perf_counter()
        result = renderer.render(
            source, edl,
            CropArtifact(source_id=source.id, edl_revision_id=edl.revision_id),
            caps,
            ExportConfig(output_root=out_dir, profile=PREVIEW_PROFILE),
        )
        elapsed = time.perf_counter() - t0
        benchmarks[preset_id] = {'elapsed_s': elapsed, 'size_bytes': result.size_bytes}
        rendered_files[preset_id] = result.path

        # Verify preview check
        preview_check = verify_preview(result, source, edl, ffprobe, PREVIEW_PROFILE)
        assert all(preview_check.values()), preview_check

    # Ensure all 4 presets generated distinct ASS files
    unique_ass = {ass_files[p] for p in ass_files}
    assert len(unique_ass) == 4, "All four presets must have distinct ASS styling"


def test_three_speeds_sync_audio_and_scale_duration(tmp_path, ffmpeg, ffprobe):
    """Verifies that 1x, 1.25x, and 1.5x scale duration accurately and synchronize audio with pitch preservation."""
    work = tmp_path / 'speeds_test'
    work.mkdir()
    source_file = work / 'source.mp4'
    _generate_synthetic_video(ffmpeg, source_file, duration_sec=3.0)
    source_raw = Source(local_path=source_file, sha256='0'*64, duration_us=3_000_000)
    source = probe_source(source_raw, ffprobe)

    source_duration_us = 3_000_000
    benchmarks = {}

    for speed, expected_dur_us, (s_num, s_den) in [
        ('1x', 3_000_000, (1, 1)),
        ('1.25x', 2_400_000, (5, 4)),
        ('1.5x', 2_000_000, (3, 2)),
    ]:
        edl = EDLArtifact(
            source_id=source.id,
            transcript_id=uuid4(),
            spans=[Span(
                source_start_us=0,
                source_end_us=source_duration_us,
                output_start_us=0,
                output_end_us=expected_dur_us,
                speed_num=s_num,
                speed_den=s_den,
            )],
            duration_us=expected_dur_us,
            protected_word_ids=[],
            playback_speed=speed,
        )

        ass_path = work / f'sub_{speed}.ass'
        srt_path = work / f'sub_{speed}.srt'
        generate_ass_from_captions(
            [{'text': 'Palavras', 'startMs': 0, 'endMs': 1000}],
            str(ass_path),
        )
        srt_path.write_text('1\n00:00:00,000 --> 00:00:01,000\nPalavras sincronizadas\n\n')

        caps = CaptionArtifact(
            transcript_id=edl.transcript_id,
            edl_revision_id=edl.revision_id,
            revision_id=uuid4(),
            style_id='karaoke_yellow',
            words=[],
            ass_path=ass_path,
            srt_path=srt_path,
            font='Arial',
        )

        out_dir = work / f'out_{speed}'
        renderer = FFmpegRenderer(ffmpeg)
        t0 = time.perf_counter()
        result = renderer.render(
            source, edl,
            CropArtifact(source_id=source.id, edl_revision_id=edl.revision_id),
            caps,
            ExportConfig(output_root=out_dir, profile=FINAL_PROFILE, playback_speed=speed),
        )
        elapsed = time.perf_counter() - t0
        benchmarks[speed] = {'elapsed_s': elapsed, 'size_bytes': result.size_bytes}

        qa = verify_render(result, source, edl, ffprobe, ffmpeg)
        assert qa.technical_pass, f"Speed {speed} failed validation: {qa.checks}"

        # Probe actual stream durations
        probed = probe_source(Source(local_path=result.path, sha256='0'*64, duration_us=expected_dur_us), ffprobe)
        actual_dur_us = probed.duration_us
        # Check that duration matches expected output duration within 100ms tolerance
        assert abs(actual_dur_us - expected_dur_us) <= 100_000, f"Expected {expected_dur_us}us, got {actual_dur_us}us"


def test_opening_card_rendering_for_all_presets(tmp_path):
    """Verifies opening cards inject valid ASS styles and events across all 4 presets."""
    work = tmp_path / 'opening_test'
    work.mkdir()

    base_ass = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 384\nPlayResY: 288\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize\nStyle: Default, Arial, 20\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    for preset_id in ['karaoke_yellow', 'editorial_sober', 'documentary', 'impact']:
        ass_path = work / f'opening_{preset_id}.ass'
        ass_path.write_text(base_ass, encoding='utf-8')
        add_opening(
            path=ass_path,
            text="O QUE VOCÊ PRECISA SABER",
            duration_us=7_000_000,
            font_name="Montserrat ExtraBold",
            preset_id=preset_id,
        )
        content = ass_path.read_text(encoding='utf-8')
        assert 'Style: Opening' in content
        assert 'O QUE VOCÊ PRECISA SABER' in content
        if preset_id == 'karaoke_yellow':
            assert '&H0000CCFF' in content
        elif preset_id == 'documentary':
            assert '&H00803010' in content or 'pos(' in content
        elif preset_id == 'impact':
            assert '&H10365AFF' in content or 't(' in content


def test_revision_isolation_and_approval_not_inherited(tmp_path):
    """Verifies that changing preset or speed creates isolated revisions without inheriting approval."""
    import uuid
    from engine.pipeline.artifacts import object_hash

    base_id = uuid.uuid4()

    # Recipe with 1x and karaoke_yellow
    recipe_1x = {'captions': {'preset_id': 'karaoke_yellow'}, 'playback_speed': '1x'}
    rid_1x = uuid.uuid5(base_id, object_hash(recipe_1x))

    # Recipe with 1.25x and karaoke_yellow
    recipe_125x = {'captions': {'preset_id': 'karaoke_yellow'}, 'playback_speed': '1.25x'}
    rid_125x = uuid.uuid5(base_id, object_hash(recipe_125x))

    # Recipe with 1x and documentary
    recipe_doc = {'captions': {'preset_id': 'documentary'}, 'playback_speed': '1x'}
    rid_doc = uuid.uuid5(base_id, object_hash(recipe_doc))

    # All three recipes must have unique presentation identities
    assert rid_1x != rid_125x
    assert rid_1x != rid_doc
    assert rid_125x != rid_doc

    # Check reviews: approving revision 1 does not approve revision 2
    from engine.editorial.review import record_review, current_review
    from engine.contracts import EditorialChecks

    folder_1 = tmp_path / 'revisions' / str(rid_1x)
    folder_2 = tmp_path / 'revisions' / str(rid_125x)
    folder_1.mkdir(parents=True)
    folder_2.mkdir(parents=True)

    # Record review decision for revision 1
    checks = EditorialChecks(
        completeness=True,
        context=True,
        qualifications=True,
        words_and_boundaries=True,
        audiovisual=True,
    )
    hash_1x = "a" * 64
    hash_125x = "b" * 64
    decision = record_review(
        revision_id=rid_1x,
        decision='approved',
        checks=checks,
        notes='Approved cut 1',
        content_hash=hash_1x,
    )
    (folder_1 / 'review.json').write_text(decision.model_dump_json(), encoding='utf-8')

    # Revision 1 with matching hash and technical_pass=True is 'approved'
    status_1, _ = current_review(folder_1, rid_1x, hash_1x, technical_pass=True)
    assert status_1 == 'approved'

    # Revision 2 (1.25x) has no review.json and must return 'needs_review'
    status_2, _ = current_review(folder_2, rid_125x, hash_125x, technical_pass=True)
    assert status_2 == 'needs_review'

    # Even if review.json from rev 1 is copied to rev 2, revision_id and content_hash mismatch -> 'stale_review', never 'approved'
    (folder_2 / 'review.json').write_text(decision.model_dump_json(), encoding='utf-8')
    status_copied, _ = current_review(folder_2, rid_125x, hash_125x, technical_pass=True)
    assert status_copied == 'stale_review'


