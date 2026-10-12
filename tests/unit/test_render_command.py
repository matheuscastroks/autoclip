from uuid import uuid4
from pathlib import Path
import pytest

def setup_render(tmp_path):
    from engine.contracts import Source,Span,EDLArtifact,CropArtifact,CaptionArtifact,ExportConfig
    s=Source(sha256='a'*64,local_path=tmp_path/'source.mp4',duration_us=2_000_000,probe={'video_origin_us':0,'video_stream_index':0,'audio_stream_index':1})
    e=EDLArtifact(source_id=s.id,transcript_id=uuid4(),spans=[Span(source_start_us=0,source_end_us=2_000_000,output_start_us=0,output_end_us=2_000_000)],duration_us=2_000_000,protected_word_ids=[])
    c=CaptionArtifact(transcript_id=e.transcript_id,edl_revision_id=e.revision_id,revision_id=uuid4(),words=[],ass_path=tmp_path/'captions.ass',srt_path=tmp_path/'captions.srt',font='Arial')
    c.ass_path.write_text('[Script Info]\n',encoding='utf-8');c.srt_path.write_text('')
    return s,e,CropArtifact(source_id=s.id,edl_revision_id=e.revision_id),c,ExportConfig(output_root=tmp_path/'output')

def test_render_uses_cpu_and_no_shell(tmp_path):
    from engine.render.ffmpeg import FFmpegRenderer
    seen=[]
    def fake(cmd,**kwargs):
        seen.append((cmd,kwargs));Path(cmd[-1]).write_bytes(b'output');return type('Result',(),{'returncode':0,'stderr':''})()
    result=FFmpegRenderer(Path('ffmpeg'),run=fake).render(*setup_render(tmp_path))
    assert result.size_bytes>0 and 'libx264' in seen[0][0] and 'h264_nvenc' not in seen[0][0]
    assert seen[0][1].get('shell',False) is False
    graph=seen[0][0][seen[0][0].index('-filter_complex')+1]
    assert 'boxblur' not in graph and 'overlay' not in graph and 'split=2' not in graph
    assert 'crop=1080:1920' in graph and 'ass=' in graph

def test_partial_render_is_never_completed(tmp_path):
    from engine.render.ffmpeg import FFmpegRenderer
    from engine.contracts import PipelineError
    def fake(cmd,**kw): Path(cmd[-1]).write_bytes(b'partial');return type('Result',(),{'returncode':1,'stderr':'error'})()
    args=setup_render(tmp_path)
    with pytest.raises(PipelineError): FFmpegRenderer(Path('ffmpeg'),run=fake).render(*args)
    assert not list((tmp_path/'output').glob('*.mp4'))
