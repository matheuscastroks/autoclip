import subprocess,json
from uuid import uuid4
from engine.contracts import Span,EDLArtifact,CropArtifact,CaptionArtifact,ExportConfig
from engine.media.importer import import_source
from engine.media.probe import probe_source
from engine.render.ffmpeg import FFmpegRenderer
from engine.render.verify import verify_render

def test_actual_pixels_are_center_crop_without_horizontal_foreground(tmp_path,ffmpeg,ffprobe):
    original=tmp_path/'bands.mp4'
    subprocess.run([str(ffmpeg),'-v','error','-y','-f','lavfi','-i','color=c=green:size=320x180:rate=30:duration=2,drawbox=x=0:y=0:w=100:h=180:color=red:t=fill,drawbox=x=220:y=0:w=100:h=180:color=blue:t=fill','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-c:a','aac',str(original)],check=True)
    source=probe_source(import_source(str(original),tmp_path/'project'),ffprobe)
    edl=EDLArtifact(source_id=source.id,transcript_id=uuid4(),spans=[Span(source_start_us=0,source_end_us=2_000_000,output_start_us=0,output_end_us=2_000_000)],duration_us=2_000_000,protected_word_ids=[])
    ass=tmp_path/'captions.ass';srt=tmp_path/'captions.srt'
    ass.write_text('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Arial,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,180,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\nDialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,LEGENDA\n',encoding='utf-8');srt.write_text('')
    caps=CaptionArtifact(transcript_id=edl.transcript_id,edl_revision_id=edl.revision_id,revision_id=uuid4(),words=[],ass_path=ass,srt_path=srt,font='Arial')
    rendered=FFmpegRenderer(ffmpeg).render(source,edl,CropArtifact(source_id=source.id,edl_revision_id=edl.revision_id),caps,ExportConfig(output_root=tmp_path/'out'))
    assert verify_render(rendered,source,edl,ffprobe,ffmpeg).technical_pass
    pixels=subprocess.run([str(ffmpeg),'-v','error','-ss','0.5','-i',str(rendered.path),'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True).stdout
    assert len(pixels)==1080*1920*3
    # Horizontal overlay would bring the red band back at the middle left.
    for x,y in [(100,960),(980,960),(100,200),(980,1800)]:
        r,g,b=pixels[(y*1080+x)*3:(y*1080+x)*3+3];assert g>r+60 and g>b+60
    # Burned-in subtitle pixels are present near the bottom.
    bottom=pixels[(1650*1080)*3:(1800*1080)*3]
    assert any(bottom[i]>210 and bottom[i+1]>210 and bottom[i+2]>210 for i in range(0,len(bottom),3))
