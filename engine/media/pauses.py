"""CPU-only conservative verification: speech VAD AND quiet audio peaks."""
import wave
import numpy as np
from engine.contracts import PauseVerification,Interval


def detect_verified_silences(audio,config,*,speech_detector=None,cancelled=lambda:False):
    result=PauseVerification(source_id=audio.source_id,source_sha256=audio.source_sha256,audio_sha256=audio.sha256)
    if not config.enabled:return result
    try:
        from engine.pipeline.artifacts import file_hash
        if file_hash(audio.path)!=audio.sha256:raise ValueError('Audio changed')
        with wave.open(str(audio.path),'rb') as stream:
            if (stream.getnchannels(),stream.getsampwidth(),stream.getframerate())!=(1,2,16000):raise ValueError('Expected canonical mono PCM16')
            samples=np.frombuffer(stream.readframes(stream.getnframes()),dtype='<i2').astype(np.float32)/32768
        if not len(samples):raise ValueError('Empty audio')
        if cancelled():
            from engine.contracts import PipelineError
            raise PipelineError('CANCELLED','pauses','Cancelled')
        if speech_detector is None:
            from faster_whisper.vad import get_speech_timestamps,VadOptions
            speech_detector=lambda a:get_speech_timestamps(a,VadOptions(threshold=.35,min_speech_duration_ms=0,min_silence_duration_ms=200,speech_pad_ms=250))
        speech=speech_detector(samples)
        size=320  # 20 ms; a frame must be entirely quiet to be removable.
        count=len(samples)//size
        quiet=np.max(np.abs(samples[:count*size].reshape(count,size)),axis=1)<=10**(config.noise_db/20)
        for segment in speech:
            a=max(0,int(segment['start'])//size);b=min(count,(int(segment['end'])+size-1)//size)
            quiet[a:b]=False
        boundaries=np.flatnonzero(np.diff(np.r_[False,quiet,False].astype(np.int8)))
        for a,b in zip(boundaries[::2],boundaries[1::2]):
            start,end=int(a)*20_000,min(int(b)*20_000,audio.duration_us)
            if end-start>=config.min_pause_us:result.silences.append(Interval(start_us=start,end_us=end))
    except Exception as exc:
        if getattr(exc,'code',None)=='CANCELLED':raise
        result.silences=[]
        result.warnings=['Verificação local de pausas indisponível. Áudio contínuo preservado.']
    return result
