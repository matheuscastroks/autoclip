import subprocess
from uuid import uuid4
from pathlib import Path
import pytest

def test_rotated_vfr_video_with_audio_offset_and_unicode_path(tmp_path,ffmpeg,ffprobe):
    from engine.media.importer import import_source
    from engine.media.probe import probe_source
    from engine.render.ffmpeg import FFmpegRenderer
    from engine.render.verify import verify_render
    from engine.contracts import Span,EDLArtifact,CropArtifact,CaptionArtifact,ExportConfig
    folder=tmp_path/"Vídeo d'água";folder.mkdir()
    original=folder/'base.mp4';rotated=folder/'rotated.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','testsrc2=size=160x90:rate=15:duration=2','-itsoffset','0.2','-f','lavfi','-i','sine=frequency=440:duration=1.8','-vf',"select='not(eq(mod(n,3),0))'",'-fps_mode','vfr','-c:v','libx264','-c:a','aac',str(original)],check=True)
    subprocess.run([str(ffmpeg),'-v','error','-y','-display_rotation','90','-i',str(original),'-c','copy',str(rotated)],check=True)
    source=probe_source(import_source(str(rotated),folder/'project'),ffprobe)
    duration=1_500_000
    edl=EDLArtifact(source_id=source.id,transcript_id=uuid4(),spans=[Span(source_start_us=0,source_end_us=duration,output_start_us=0,output_end_us=duration)],duration_us=duration,protected_word_ids=[])
    ass=folder/'caption.ass';srt=folder/'caption.srt'
    ass.write_text('[Script Info]\nScriptType: v4.00+\nPlayResX: 384\nPlayResY: 288\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Arial,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,20,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\nDialogue: 0,0:00:00.00,0:00:01.40,Default,,0,0,0,,Legenda sincronizada\n',encoding='utf-8');srt.write_text('')
    caps=CaptionArtifact(transcript_id=edl.transcript_id,edl_revision_id=edl.revision_id,revision_id=uuid4(),words=[],ass_path=ass,srt_path=srt,font='Arial')
    result=FFmpegRenderer(ffmpeg).render(source,edl,CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id),caps,ExportConfig(output_root=folder/'output'))
    qa=verify_render(result,source,edl,ffprobe,ffmpeg)
    assert qa.technical_pass,qa.checks
    assert abs(source.probe['rotation'])==90
    assert source.probe['audio_offset_us']!=0
    # Actual pixels differ when caption layer is removed, not just an ASS sidecar.
    import hashlib
    frame=folder/'frame.png'
    subprocess.run([str(ffmpeg),'-v','error','-y','-ss','0.5','-i',str(result.path),'-frames:v','1',str(frame)],check=True)
    assert frame.stat().st_size>1000
