import json,time
from pathlib import Path
from engine.pipeline.artifacts import object_hash,write_artifact,read_artifact,atomic_json,file_hash,confined
from engine.contracts import ArtifactRef,PipelineError

class StageCache:
    def __init__(self,root:Path):
        self.root=Path(root).resolve();(self.root/'stages').mkdir(parents=True,exist_ok=True)
        self.reused=[]

    def run(self,stage:str,inputs:dict,producer,model):
        key=object_hash({'stage':stage,'schema_version':'1.0','inputs':inputs})
        path=confined(self.root,f'stages/{stage}/{key}.json')
        if path.is_file():
            try:
                saved=json.loads(path.read_text(encoding='utf-8'))
                if saved['status']=='completed':
                    ref=ArtifactRef.model_validate(saved['artifact'])
                    result=read_artifact(ref,self.root,model)
                    for output in saved.get('files',[]):
                        f=Path(output['path'])
                        if not f.is_relative_to(self.root) or file_hash(f)!=output['sha256']: raise ValueError('missing/corrupt output file')
                    self.reused.append(stage);return result
            except (ValueError,KeyError,OSError,PipelineError): pass
        started=time.monotonic()
        atomic_json(path,{'schema_version':'1.0','stage':stage,'cache_key':key,'status':'running','inputs':inputs})
        try:
            result=producer()
            result=model.model_validate(result.model_dump(mode='json'))
            ref=write_artifact(result,stage,self.root)
            files=[]
            for name in ['path','ass_path','srt_path']:
                value=getattr(result,name,None)
                if value is not None:
                    file=Path(value).resolve()
                    if not file.is_relative_to(self.root): raise PipelineError('UNSAFE_PATH','storage','Generated output outside project root.')
                    files.append({'path':str(file),'sha256':file_hash(file)})
            atomic_json(path,{'schema_version':'1.0','stage':stage,'cache_key':key,'status':'completed','inputs':inputs,'artifact':ref,'files':files,'wall_ms':round((time.monotonic()-started)*1000)})
            return result
        except BaseException as exc:
            error=exc.as_dict() if isinstance(exc,PipelineError) else {'code':'CANCELLED' if isinstance(exc,KeyboardInterrupt) else 'STAGE_FAILED','message':'Stage interrupted or failed; no valid checkpoint.'}
            atomic_json(path,{'schema_version':'1.0','stage':stage,'cache_key':key,'status':'failed','inputs':inputs,'error':error})
            raise
