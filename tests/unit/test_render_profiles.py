from pathlib import Path

import pytest

from test_render_command import setup_render
from engine.contracts import CropPoint, ExportConfig
from engine.media.face_tracking import crop_expression
from engine.render.ffmpeg import FFmpegRenderer


def test_preview_profile_controls_encoder_without_changing_timeline(tmp_path):
    from engine.contracts import PREVIEW_PROFILE, FINAL_PROFILE

    assert ExportConfig(output_root=tmp_path).profile == FINAL_PROFILE
    source, edl, crop, captions, _ = setup_render(tmp_path)
    commands = []

    def fake(command, **kwargs):
        commands.append(command)
        Path(command[-1]).write_bytes(b'video')
        return type('Result', (), {'returncode': 0, 'stderr': ''})()

    for profile in (PREVIEW_PROFILE, FINAL_PROFILE):
        FFmpegRenderer(Path('ffmpeg'), run=fake).render(
            source, edl, crop, captions,
            ExportConfig(output_root=tmp_path / profile.name, profile=profile),
        )
    preview, final = commands
    for command, dimensions, preset, crf, audio in (
        (preview, '540:960', 'veryfast', '30', '96k'),
        (final, '1080:1920', 'medium', '20', '192k'),
    ):
        graph = command[command.index('-filter_complex') + 1]
        assert f'scale={dimensions}' in graph and f'crop={dimensions}' in graph
        assert command[command.index('-preset') + 1] == preset
        assert command[command.index('-crf') + 1] == crf
        assert command[command.index('-b:a') + 1] == audio
        assert command[command.index('-t') + 1] == '2.000000'
        assert 'ass=filename=captions.ass' in graph
    assert preview[preview.index('-filter_complex') + 1].split('[vbase]')[0] == final[final.index('-filter_complex') + 1].split('[vbase]')[0]


@pytest.mark.parametrize('center', [.1, .5, .9])
def test_face_crop_is_resolution_relative(center):
    points = [CropPoint(output_us=0, center_x=center)]
    expressions = [crop_expression(points, width=width) for width in (540, 1080)]
    positions = []
    for width, expression in zip((540, 1080), expressions):
        assert f'iw-{width}' in expression
        positions.append(eval(expression, {'__builtins__': {}}, {'max': max, 'min': min, 'iw': width * 3}) / width)
    assert positions[0] == pytest.approx(positions[1])


def test_profiles_validate_aspect_ratio_and_legacy_crf(tmp_path):
    from engine.contracts import RenderProfile

    with pytest.raises(ValueError):
        RenderProfile(name='preview', width=540, height=1920)
    assert ExportConfig(output_root=tmp_path, crf=22).profile.crf == 22
