import subprocess
import pytest

def test_probe_rotation_vfr_and_audio_offset_are_recorded(tmp_path,ffmpeg,ffprobe):
    from engine.media.importer import import_source
    from engine.media.probe import probe_source
    from engine.media.audio import extract_audio
    p = tmp_path/"Vídeo d'água 01.mp4"
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','testsrc2=size=160x90:rate=15:duration=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-c:a','aac',str(p)],check=True)
    source = probe_source(import_source(str(p),tmp_path/'project'),ffprobe)
    assert source.probe['fps'] == {'num':15,'den':1}
    assert 'video_origin_us' in source.probe
    assert 'audio_offset_us' in source.probe
    audio = extract_audio(source,ffmpeg,tmp_path/'project')
    assert audio.path.exists() and audio.duration_us > 1_900_000
    assert audio.sample_rate == 16000 and audio.channels == 1

def test_no_audio_is_explicit_error(tmp_path,ffmpeg,ffprobe):
    from engine.media.importer import import_source
    from engine.media.probe import probe_source
    from engine.contracts import PipelineError
    p=tmp_path/'silent.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','color=size=160x90:duration=1','-c:v','libx264',str(p)],check=True)
    with pytest.raises(PipelineError) as e: probe_source(import_source(str(p),tmp_path/'project'),ffprobe)
    assert e.value.code == 'NO_AUDIO'
