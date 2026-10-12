import importlib.metadata,sys
from pathlib import Path
from engine.contracts import AudioArtifact,ASRConfig,TranscriptArtifact,Word,Segment,PipelineError
from engine.pipeline.artifacts import file_hash
from vendor.openshorts.transcribe_backends import transcribe_explicit


def configure_utf8():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            try: stream.reconfigure(encoding='utf-8',errors='replace')
            except (ValueError,AttributeError): pass

class OpenShortsTranscriber:
    def __init__(self,model_factory=None): self.model_factory=model_factory

    def transcribe(self,audio:AudioArtifact,config:ASRConfig) -> TranscriptArtifact:
        configure_utf8()
        factory=self.model_factory
        if factory is None:
            if not (config.model_path/'model.bin').is_file():
                raise PipelineError('MODEL_MISSING','transcribe','Whisper model.bin missing; provision the multilingual small model.')
            from faster_whisper import WhisperModel
            factory=WhisperModel
        try:
            model=factory(str(config.model_path),device=config.device,compute_type=config.compute_type)
            raw=transcribe_explicit(str(audio.path),model,language=config.language)
        except Exception as exc:
            raise PipelineError('ASR_FAILED','transcribe','ASR failed locally; check model/runtime compatibility.') from exc
        words=[];segments=[]
        for segment in raw['segments']:
            ids=[]
            for w in segment.get('words',[]):
                text=w['word'].strip()
                if not text: continue
                a,b=round(w['start']*1e6),round(w['end']*1e6)
                if b<=a: continue
                if b>audio.duration_us+100_000:
                    raise PipelineError('INVALID_TIMING','transcribe','Word outside source bounds.')
                wid=f'w{len(words):07d}';ids.append(wid)
                words.append(Word(id=wid,text=text,start_us=a,end_us=b,probability=w.get('probability')))
            if ids:
                segments.append(Segment(id=f's{len(segments):06d}',word_ids=ids,text=segment['text'],start_us=min(w.start_us for w in words if w.id in ids),end_us=max(w.end_us for w in words if w.id in ids)))
        if not words: raise PipelineError('NO_SPEECH','transcribe','No usable speech; no remote media fallback.')
        record={'provider':'faster-whisper','name':'small','path':str(config.model_path),'device':'cpu','compute_type':'int8','version':importlib.metadata.version('faster-whisper')}
        if (config.model_path/'model.bin').exists(): record['digest']='sha256:'+file_hash(config.model_path/'model.bin')
        return TranscriptArtifact(source_id=audio.source_id,source_sha256=audio.source_sha256,language=raw['language'],model=record,words=words,segments=segments)
