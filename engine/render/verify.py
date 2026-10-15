import subprocess,re
from pathlib import Path
from fractions import Fraction
from engine.contracts import RenderArtifact,Source,EDLArtifact,ExportValidation,PipelineError
from engine.media.probe import probe_json
from engine.pipeline.artifacts import file_hash
from engine.pipeline.cancellation import run_process

def verify_preview(render,source,edl,ffprobe,profile,cancelled=lambda:False):
    """Container/stream checks only; never substitutes for final technical QA."""
    probe=probe_json(render.path,ffprobe,cancelled)
    video=next((s for s in probe['streams'] if s['codec_type']=='video'),{})
    audio=next((s for s in probe['streams'] if s['codec_type']=='audio'),{})
    return {
        'hash':file_hash(render.path)==render.sha256,
        'size':render.path.stat().st_size==render.size_bytes,
        'dimensions':(video.get('width'),video.get('height'))==(profile.width,profile.height),
        'duration':abs(round(float(probe['format']['duration'])*1e6)-edl.duration_us)<=33_355,
        'fps':Fraction(video.get('avg_frame_rate','0/1'))==profile.fps,
        'video_codec':video.get('codec_name')=='h264',
        'audio':audio.get('codec_name')=='aac' and audio.get('sample_rate')=='48000',
        'revision_match':render.revision_id==edl.revision_id and source.id==edl.source_id,
    }

def verify_render(render:RenderArtifact,source:Source,edl:EDLArtifact,ffprobe:Path,ffmpeg:Path,cancelled=lambda:False) -> ExportValidation:
    from engine.pipeline.telemetry import active, observe
    from engine.pipeline.progress import RenderProgress
    observe('verify',0,edl.duration_us*2,'media_us')
    def monitor(offset):
        if not active():return {},[]
        parser=RenderProgress(edl.duration_us,lambda done,total:observe('verify',offset+done,total*2,'media_us'))
        return {'on_stdout_line':parser.line},['-progress','pipe:1','-nostats']
    probe=probe_json(render.path,ffprobe,cancelled)
    v=next((s for s in probe['streams'] if s['codec_type']=='video'),{})
    a=next((s for s in probe['streams'] if s['codec_type']=='audio'),{})
    extra,args=monitor(0)
    decoded=run_process([str(ffmpeg),*args,'-nostdin','-v','error','-i',str(render.path),'-f','null','-'],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8',**extra)
    extra,args=monitor(edl.duration_us)
    levels=run_process([str(ffmpeg),*args,'-nostdin','-v','info','-i',str(render.path),'-vn','-af','volumedetect','-f','null','-'],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8',**extra)
    match=re.search(r'max_volume:\s*([-+\d.]+|[-+]?inf)\s*dB',levels.stderr or '')
    peak=float(match.group(1)) if match else float('-inf')
    duration=round(float(probe['format']['duration'])*1e6)
    checks={'hash':file_hash(render.path)==render.sha256,'size':render.path.stat().st_size==render.size_bytes,'decoded':decoded.returncode==0,'dimensions':v.get('width')==1080 and v.get('height')==1920,'video_codec':v.get('codec_name')=='h264','pixel_format':v.get('pix_fmt')=='yuv420p','audio':a.get('codec_name')=='aac' and a.get('sample_rate')=='48000','fps':Fraction(v.get('avg_frame_rate','0/1'))==30,'duration':abs(duration-edl.duration_us)<=33_355,'non_silent':levels.returncode==0 and peak>-80,'orientation':not any(s.get('rotation',0) for s in v.get('side_data_list',[])),'source_match':source.id==edl.source_id,'revision_match':render.revision_id==edl.revision_id}
    observe('verify',finished=all(checks.values()))
    return ExportValidation(revision_id=edl.revision_id,technical_pass=all(checks.values()),checks=checks,warnings=['Editorial integrity requires human review; technical checks do not prove meaning.'])
