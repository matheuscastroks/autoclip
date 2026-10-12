import json, os, shutil, subprocess
from pathlib import Path
from fractions import Fraction
from engine.contracts import Source, PipelineError
from engine.pipeline.cancellation import run_process


def locate_tools():
    found=shutil.which('ffmpeg')
    candidates=[Path(found)] if found else []
    candidates += list((Path.home()/'AppData/Local/Microsoft/WinGet/Packages').glob('Gyan.FFmpeg_*/**/ffmpeg.exe'))
    for ffmpeg in candidates:
        ffprobe=ffmpeg.with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
        if ffmpeg.is_file() and ffprobe.is_file(): return ffmpeg,ffprobe
    raise PipelineError('TOOL_MISSING','doctor','FFmpeg/ffprobe not found; pass explicit paths.')

def probe_json(path: Path,ffprobe: Path,cancelled=lambda:False):
    r=run_process([str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(path)],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8',timeout_s=30)
    if r.returncode: raise PipelineError('SOURCE_UNAVAILABLE','probe','ffprobe could not decode media.')
    return json.loads(r.stdout)

def probe_source(source: Source,ffprobe: Path) -> Source:
    raw=probe_json(source.local_path,ffprobe)
    video=next((s for s in raw['streams'] if s['codec_type']=='video'),None)
    audio=next((s for s in raw['streams'] if s['codec_type']=='audio'),None)
    if not video: raise PipelineError('NO_VIDEO','probe','No video stream.')
    if not audio: raise PipelineError('NO_AUDIO','probe','No audio stream; no speech fallback to remote media.')
    fps=Fraction(video.get('avg_frame_rate') or '30/1')
    if not fps: fps=Fraction(30)
    origin=round(float(video.get('start_time',raw['format'].get('start_time',0)))*1e6)
    audio_start=round(float(audio.get('start_time',raw['format'].get('start_time',0)))*1e6)
    duration=round(float(video.get('duration') or raw['format']['duration'])*1e6)
    rotation=int(next((s['rotation'] for s in video.get('side_data_list',[]) if 'rotation' in s),video.get('tags',{}).get('rotate',0)))
    source=source.model_copy(deep=True)
    source.duration_us=duration
    source.probe={'raw':raw,'fps':{'num':fps.numerator,'den':fps.denominator},'video_origin_us':origin,'audio_offset_us':audio_start-origin,'rotation':rotation,'width':video['width'],'height':video['height'],'video_stream_index':video['index'],'audio_stream_index':audio['index'],'time_base':video.get('time_base')}
    return source
