import json
from pathlib import Path
from engine.contracts import Source,TranscriptArtifact,ProjectRun

def read_json(path:Path,default=None):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return default

def project_detail(row:dict)->dict:
    root=Path(row['path']);warnings=[];source=None;transcript=None;state=None
    for name,model in [('source',Source),('transcript',TranscriptArtifact),('project',ProjectRun)]:
        path=root/(name+'.json')
        if path.exists():
            try:value=model.model_validate_json(path.read_bytes())
            except (OSError,ValueError):warnings.append(f'Arquivo {name}.json inválido. Os demais dados foram preservados.');value=None
            if name=='source':source=value
            elif name=='transcript':transcript=value
            else:state=value
    manual=(root/'manual-check.json').exists()
    status=state.status if state else ('transcribed' if transcript else 'imported')
    if manual:status='manual_preview'
    if not source:status='pending_import'
    if source and not source.local_path.is_file():warnings.append('O vídeo original não foi encontrado no caminho registrado.')
    error=read_json(root/'last-error.json')
    return {**row,'schema_version':'1.0','title':source.original_title if source else row['name'],
        'source':source.model_dump(mode='json') if source else None,'duration_us':source.duration_us if source else 0,
        'status':status,'has_transcript':transcript is not None,'word_count':len(transcript.words) if transcript else 0,
        'revisions':state.revisions if state and not manual else [],'is_manual':manual,'warnings':warnings,'error':error,
        'has_analysis':bool((read_json(root/'analysis.json') or {}).get('complete')),
        'updated_at':max((p.stat().st_mtime for p in root.glob('*.json')),default=0)}

def discover(store,workspace):
    directory=Path(workspace)/'poc-projects'
    if directory.exists():
        for root in directory.iterdir():
            if root.is_dir() and (root/'source.json').is_file():
                try:store.register(root)
                except (ValueError,OSError):pass
