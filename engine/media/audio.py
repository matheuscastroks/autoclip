import subprocess, uuid, wave
from pathlib import Path
from engine.contracts import AudioArtifact,Source,PipelineError
from engine.pipeline.artifacts import file_hash
from engine.pipeline.cancellation import run_process


def extract_audio(source: Source,ffmpeg: Path,project_root: Path,cancelled=lambda:False) -> AudioArtifact:
    root=Path(project_root)/'media';root.mkdir(parents=True,exist_ok=True)
    path=root/f'audio-{source.sha256[:16]}.wav'
    temp=root/(uuid.uuid4().hex+'.wav')
    origin=source.probe.get('video_origin_us',0)/1e6
    filters=f'atrim=start={origin:.6f}:end={origin+source.duration_us/1e6:.6f},asetpts=PTS-{origin:.6f}/TB,aresample=16000:async=1:first_pts=0,apad,atrim=duration={source.duration_us/1e6:.6f}'
    try:
        r=run_process([str(ffmpeg),'-nostdin','-v','error','-y','-copyts','-i',str(source.local_path),'-map',f"0:{source.probe['audio_stream_index']}",'-vn','-af',filters,'-ac','1','-ar','16000','-c:a','pcm_s16le',str(temp)],cancelled=cancelled,capture_output=True,text=True,encoding='utf-8')
        if r.returncode: raise PipelineError('AUDIO_FAILED','audio','FFmpeg audio extraction failed.')
        with wave.open(str(temp)) as wav: duration=round(wav.getnframes()/wav.getframerate()*1e6)
        if duration<=0: raise PipelineError('AUDIO_FAILED','audio','Empty decoded audio.')
        temp.replace(path)
        return AudioArtifact(source_id=source.id,source_sha256=source.sha256,path=path.resolve(),sha256=file_hash(path),duration_us=duration,source_origin_us=source.probe.get('video_origin_us',0))
    finally: temp.unlink(missing_ok=True)
