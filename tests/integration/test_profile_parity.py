import json
import subprocess

from engine.contracts import (
    PREVIEW_PROFILE, FINAL_PROFILE, CaptionConfig, CaptionRevision, CropArtifact,
    CropPoint, EDLArtifact, ExportConfig, Span, TranscriptArtifact, Word,
)
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
from engine.media.importer import import_source
from engine.media.probe import probe_source, probe_json
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_render
from engine.pipeline.fingerprints import resolve_font


def test_synthetic_profiles_share_edl_audio_and_burned_captions(tmp_path, ffmpeg, ffprobe):
    original = tmp_path / 'synthetic.mp4'
    subprocess.run([str(ffmpeg), '-v', 'error', '-y', '-f', 'lavfi', '-i',
                    'color=c=0x203040:size=640x360:rate=30:duration=3', '-f', 'lavfi', '-i',
                    'sine=frequency=440:duration=3', '-c:v', 'libx264', '-c:a', 'aac',
                    str(original)], check=True)
    source = probe_source(import_source(str(original), tmp_path / 'project'), ffprobe)
    transcript = TranscriptArtifact(source_id=source.id, source_sha256=source.sha256, words=[
        Word(id='one', text='Legenda', start_us=200_000, end_us=700_000),
        Word(id='two', text='sincronizada', start_us=1_700_000, end_us=2_200_000),
    ])
    edl = EDLArtifact(source_id=source.id, transcript_id=transcript.transcript_id,
                      duration_us=2_000_000, protected_word_ids=['one', 'two'], spans=[
        Span(source_start_us=0, source_end_us=1_000_000, output_start_us=0, output_end_us=1_000_000),
        Span(source_start_us=1_500_000, source_end_us=2_500_000, output_start_us=1_000_000, output_end_us=2_000_000),
    ])
    caps = OpenShortsCaptionBuilder(tmp_path / 'captions').build(
        transcript, edl, CaptionRevision(), CaptionConfig(
            font_path=resolve_font(None, 'Montserrat ExtraBold'), opening_text='Título de teste'))
    crop = CropArtifact(source_id=source.id, edl_revision_id=edl.revision_id, mode='face-track', points=[
        CropPoint(output_us=0, center_x=.3), CropPoint(output_us=1_000_000, center_x=.7),
    ])
    original_edl = edl.model_dump_json()
    for profile in (PREVIEW_PROFILE, FINAL_PROFILE):
        result = FFmpegRenderer(ffmpeg).render(source, edl, crop, caps,
            ExportConfig(output_root=tmp_path / profile.name, profile=profile))
        probe = probe_json(result.path, ffprobe)
        video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        assert (video['width'], video['height']) == (profile.width, profile.height)
        assert abs(float(probe['format']['duration']) - 2) < .034
        assert audio['sample_rate'] == '48000'
        # ASS is burned in both outputs, not merely emitted as a sidecar.
        raw = subprocess.run([str(ffmpeg), '-v', 'error', '-ss', '0.5', '-i', str(result.path),
            '-frames:v', '1', '-vf', 'scale=270:480', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
            check=True, capture_output=True).stdout
        assert any(r > 150 and g > 130 for r, g in zip(raw[0::3], raw[1::3]))
        if profile.name == 'final':
            qa = verify_render(result, source, edl, ffprobe, ffmpeg)
            assert qa.technical_pass, json.dumps(qa.checks)
    assert edl.model_dump_json() == original_edl
    assert caps.words[1].start_us == 1_200_000
