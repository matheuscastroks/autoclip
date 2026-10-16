from uuid import uuid4
from pathlib import Path
import pytest
from pydantic import ValidationError

from test_gemini import transcript, payload
from test_render_command import setup_render
from engine.contracts import (
    Source, Candidate, CaptionConfig, CaptionRevision, ExportConfig,
    Span, EDLArtifact, PipelineError,
)
from engine.editorial.edl import plan_continuous_edit, source_at, output_at
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.render.presets import (
    PLAYBACK_SPEED_RATIONAL,
    validate_playback_speed,
    speed_ratio_to_label,
)
from engine.render.ffmpeg import FFmpegRenderer


def test_speed_validation_accepts_only_supported_speeds():
    assert validate_playback_speed('1x') == '1x'
    assert validate_playback_speed('1.25x') == '1.25x'
    assert validate_playback_speed('1.5x') == '1.5x'
    assert validate_playback_speed(None) == '1x'
    with pytest.raises(ValueError):
        validate_playback_speed('2x')
    with pytest.raises(ValueError):
        validate_playback_speed('0.75x')
    with pytest.raises(ValueError):
        validate_playback_speed('fast')


def test_span_enforces_rational_speed_ratios_and_output_duration():
    # 1x
    Span(source_start_us=0, source_end_us=1000, output_start_us=0, output_end_us=1000, speed_num=1, speed_den=1)
    # 1.25x (5/4) -> 1000 * 4 // 5 = 800
    Span(source_start_us=0, source_end_us=1000, output_start_us=0, output_end_us=800, speed_num=5, speed_den=4)
    # 1.5x (3/2) -> 1200 * 2 // 3 = 800
    Span(source_start_us=0, source_end_us=1200, output_start_us=0, output_end_us=800, speed_num=3, speed_den=2)

    # Invalid speed ratio
    with pytest.raises(ValidationError):
        Span(source_start_us=0, source_end_us=1000, output_start_us=0, output_end_us=500, speed_num=2, speed_den=1)

    # Output duration mismatch for given speed
    with pytest.raises(ValidationError):
        Span(source_start_us=0, source_end_us=1000, output_start_us=0, output_end_us=1000, speed_num=5, speed_den=4)


def test_plan_continuous_edit_scales_timeline_for_each_speed(tmp_path):
    t = transcript()
    s = Source(id=t.source_id, sha256=t.source_sha256, local_path=tmp_path / 's.mp4', duration_us=40_000_000)
    c = Candidate.model_validate(payload(t)['candidates'][0])

    edl_1x = plan_continuous_edit(c, t, s, playback_speed='1x')
    edl_125 = plan_continuous_edit(c, t, s, playback_speed='1.25x')
    edl_15 = plan_continuous_edit(c, t, s, playback_speed='1.5x')

    assert edl_1x.playback_speed == '1x'
    assert edl_125.playback_speed == '1.25x'
    assert edl_15.playback_speed == '1.5x'

    # Durations must strictly follow rational scaling
    source_dur = edl_1x.spans[0].source_end_us - edl_1x.spans[0].source_start_us
    assert edl_1x.duration_us == source_dur
    assert edl_125.duration_us == source_dur * 4 // 5
    assert edl_15.duration_us == source_dur * 2 // 3

    # Output_at and source_at roundtrip with speed scaling
    mid_source = (edl_125.spans[0].source_start_us + edl_125.spans[0].source_end_us) // 2
    out_pos = output_at(edl_125, mid_source)
    assert out_pos is not None
    assert abs(source_at(edl_125, out_pos) - mid_source) <= 2


def test_ffmpeg_filtergraph_applies_atempo_and_scaled_pts(tmp_path):
    source, edl, crop, captions, config = setup_render(tmp_path)
    commands = []

    def fake(command, **kwargs):
        commands.append(command)
        Path(command[-1]).write_bytes(b'video')
        return type('Result', (), {'returncode': 0, 'stderr': ''})()

    for speed in ('1x', '1.25x', '1.5x'):
        num, den = PLAYBACK_SPEED_RATIONAL[speed]
        src_dur = 2_000_000
        out_dur = src_dur * den // num
        scaled_edl = EDLArtifact(
            source_id=source.id,
            transcript_id=edl.transcript_id,
            playback_speed=speed,
            spans=[Span(source_start_us=0, source_end_us=src_dur, output_start_us=0, output_end_us=out_dur, speed_num=num, speed_den=den)],
            duration_us=out_dur,
            protected_word_ids=[],
        )
        scaled_caps = captions.model_copy(update={'edl_revision_id': scaled_edl.revision_id})
        scaled_crop = crop.model_copy(update={'edl_revision_id': scaled_edl.revision_id})
        FFmpegRenderer(Path('ffmpeg'), run=fake).render(
            source, scaled_edl, scaled_crop, scaled_caps,
            ExportConfig(output_root=tmp_path / speed, playback_speed=speed),
        )

    cmd_1x, cmd_125, cmd_15 = commands
    graph_1x = cmd_1x[cmd_1x.index('-filter_complex') + 1]
    graph_125 = cmd_125[cmd_125.index('-filter_complex') + 1]
    graph_15 = cmd_15[cmd_15.index('-filter_complex') + 1]

    # 1x does not introduce atempo
    assert 'atempo=' not in graph_1x
    assert 'setpts=PTS-' in graph_1x

    # 1.25x has setpts *4/5 and atempo=1.25
    assert 'setpts=(PTS-0.000000/TB)*4/5' in graph_125
    assert 'atempo=1.25' in graph_125

    # 1.5x has setpts *2/3 and atempo=1.5
    assert 'setpts=(PTS-0.000000/TB)*2/3' in graph_15
    assert 'atempo=1.5' in graph_15


def test_caption_builder_syncs_words_and_preserves_7s_opening_effective_duration(tmp_path):
    t = transcript()
    s = Source(id=t.source_id, sha256=t.source_sha256, local_path=tmp_path / 's.mp4', duration_us=40_000_000)
    c = Candidate.model_validate(payload(t)['candidates'][0])
    edl_15 = plan_continuous_edit(c, t, s, playback_speed='1.5x')

    builder = OpenShortsCaptionBuilder(tmp_path)
    caps = builder.build(t, edl_15, CaptionRevision(), CaptionConfig(preset_id='karaoke_yellow', opening_text='Abertura'))

    # All caption words must lie within the accelerated EDL duration
    assert all(w.end_us <= edl_15.duration_us for w in caps.words)

    # Opening duration is preserved as 7s in the effective output timeline
    assert caps.opening_duration_us == min(edl_15.duration_us, 7_000_000)
    ass_text = caps.ass_path.read_text(encoding='utf-8')
    assert '0:00:06.70,0:00:07.00,Opening' in ass_text
