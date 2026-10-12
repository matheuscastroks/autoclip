import subprocess,wave
from uuid import uuid4

def test_multiple_spans_render_with_captions_and_preserve_audio_timing(tmp_path,ffmpeg,ffprobe):
    from engine.media.importer import import_source
    from engine.media.probe import probe_source
    from engine.contracts import EDLArtifact,Span,CropArtifact,CaptionArtifact,ExportConfig
    from engine.render.ffmpeg import FFmpegRenderer
    from engine.render.verify import verify_render
    path=tmp_path/'source.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','testsrc2=size=160x90:rate=30:duration=4','-f','lavfi','-i','sine=frequency=440:duration=4','-c:v','libx264','-c:a','aac',str(path)],check=True)
    source=probe_source(import_source(str(path),tmp_path/'project'),ffprobe)
    edl=EDLArtifact(source_id=source.id,transcript_id=uuid4(),spans=[Span(source_start_us=0,source_end_us=1_000_000,output_start_us=0,output_end_us=1_000_000),Span(source_start_us=3_000_000,source_end_us=4_000_000,output_start_us=1_000_000,output_end_us=2_000_000)],duration_us=2_000_000,protected_word_ids=[])
    ass=tmp_path/'caption.ass';ass.write_text('[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,80,80,120,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,Depois da junção\n',encoding='utf-8')
    srt=tmp_path/'caption.srt';srt.write_text('')
    caps=CaptionArtifact(transcript_id=edl.transcript_id,edl_revision_id=edl.revision_id,revision_id=uuid4(),words=[],ass_path=ass,srt_path=srt,font='Arial')
    result=FFmpegRenderer(ffmpeg).render(source,edl,CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id),caps,ExportConfig(output_root=tmp_path/'out'))
    qa=verify_render(result,source,edl,ffprobe,ffmpeg)
    assert qa.technical_pass,qa.checks

def test_local_silero_model_can_verify_quiet_pcm_without_download(tmp_path):
    from engine.contracts import AudioArtifact,PauseConfig
    from engine.pipeline.artifacts import file_hash
    from engine.media.pauses import detect_verified_silences
    path=tmp_path/'quiet.wav'
    with wave.open(str(path),'wb') as stream:stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000);stream.writeframes(b'\0\0'*48000)
    audio=AudioArtifact(source_id=uuid4(),source_sha256='a'*64,path=path,sha256=file_hash(path),duration_us=3_000_000)
    result=detect_verified_silences(audio,PauseConfig(enabled=True))
    assert not result.warnings and result.silences[0].end_us==3_000_000
