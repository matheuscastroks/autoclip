import subprocess,wave,array
from uuid import uuid4
import pytest

def media_setup(tmp_path,ffmpeg,ffprobe,*,silent=False):
    from engine.media.importer import import_source
    from engine.media.probe import probe_source
    from engine.contracts import EDLArtifact,Span,CropArtifact,CaptionArtifact,ExportConfig
    p=tmp_path/'sparse.mp4'
    tone='anullsrc=r=48000:cl=mono' if silent else 'sine=frequency=440:sample_rate=48000:duration=3'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i',"color=red:size=160x90:rate=1:duration=3,drawbox=color=green:enable='gte(t,1)':t=fill",'-f','lavfi','-i',tone,'-t','3','-c:v','libx264','-c:a','aac',str(p)],check=True)
    s=probe_source(import_source(str(p),tmp_path/'project'),ffprobe)
    e=EDLArtifact(source_id=s.id,transcript_id=uuid4(),spans=[Span(source_start_us=250_000,source_end_us=1_750_000,output_start_us=0,output_end_us=1_500_000)],duration_us=1_500_000,protected_word_ids=[])
    ass=tmp_path/'empty.ass';ass.write_text('[Script Info]\nScriptType: v4.00+\n[V4+ Styles]\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n',encoding='utf-8')
    srt=tmp_path/'empty.srt';srt.write_text('')
    c=CaptionArtifact(transcript_id=e.transcript_id,edl_revision_id=e.revision_id,revision_id=uuid4(),words=[],ass_path=ass,srt_path=srt,font='Arial')
    return s,e,CropArtifact(source_id=s.id,edl_revision_id=e.revision_id),c,ExportConfig(output_root=tmp_path/'out')

def test_vfr_between_frames_keeps_original_visual_clock(tmp_path,ffmpeg,ffprobe):
    from engine.render.ffmpeg import FFmpegRenderer
    from PIL import Image
    args=media_setup(tmp_path,ffmpeg,ffprobe)
    r=FFmpegRenderer(ffmpeg).render(*args)
    early=tmp_path/'early.png';late=tmp_path/'late.png'
    for t,p in [('0.3',early),('0.9',late)]:subprocess.run([str(ffmpeg),'-v','error','-y','-ss',t,'-i',str(r.path),'-frames:v','1',str(p)],check=True)
    red=Image.open(early).getpixel((540,960));green=Image.open(late).getpixel((540,960))
    assert red[0]>red[1]*2,red
    assert green[1]>green[0]*2,green

def test_digital_zero_audio_fails_export_qa(tmp_path,ffmpeg,ffprobe):
    from engine.render.ffmpeg import FFmpegRenderer
    from engine.render.verify import verify_render
    args=media_setup(tmp_path,ffmpeg,ffprobe,silent=True)
    r=FFmpegRenderer(ffmpeg).render(*args)
    qa=verify_render(r,args[0],args[1],ffprobe,ffmpeg)
    assert not qa.technical_pass and not qa.checks['non_silent']
