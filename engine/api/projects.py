import json
from pathlib import Path
from engine.contracts import Source,TranscriptArtifact,ProjectRun

def read_json(path:Path,default=None):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return default

def project_summary(root:Path,state:dict,job)->dict:
    analysis=read_json(root/'analysis.json',{}) or {}
    ids={str(c.get('id')) for c in analysis.get('candidates',[]) if c.get('id')}
    selection=read_json(root/'analysis-selection.json',{}) or {}
    # Reject stale selections when the analysis was replaced.
    from engine.pipeline.artifacts import object_hash
    selected=set(selection.get('candidate_ids',[])) & ids
    if selection.get('analysis_hash') and selection['analysis_hash']!=object_hash(analysis):selected=set()
    generated=set()
    for row in state.get('revisions',[]):
        rid=row.get('revision_id','')
        from uuid import UUID
        try:UUID(rid)
        except (ValueError,TypeError):continue
        folder=root/'revisions'/rid
        if (folder/'deleted.json').exists():continue
        media=Path(row.get('render_path',''))
        if not media.resolve().is_relative_to(root.resolve()) or not media.is_file():continue
        if not all((folder/name).is_file() for name in ('edl.json','captions.json')):continue
        if not all(isinstance(read_json(folder/name),dict) for name in ('edl.json','captions.json')):continue
        candidate=read_json(folder/'candidate.json',{}) or {}
        qa=read_json(folder/'qa.json',{}) or {}
        if candidate.get('id') and qa.get('technical_pass'):generated.add(str(candidate['id']))
    return {'proposed':len(ids) if analysis else None,'selected':len(selected) if analysis else None,
        'generated':len(generated),'stage':job.get('stage') if job and job.get('status') in ('pending','running','cancelling') else None}

def project_detail(row:dict,job=None)->dict:
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
    if job:
        if job['status'] in ('running','pending','cancelling'):status='processing';error=None
        elif job['status'] in ('failed','cancelled','interrupted'):status=job['status'];error=job.get('error')
        else:error=None
    return {**row,'schema_version':'1.0','title':source.original_title if source else row['name'],
        'source':source.model_dump(mode='json') if source else None,'duration_us':source.duration_us if source else 0,
        'status':status,'has_transcript':transcript is not None,'word_count':len(transcript.words) if transcript else 0,
        'revisions':state.revisions if state and not manual else [],'is_manual':manual,'warnings':warnings,'error':error,
        'has_analysis':bool((read_json(root/'analysis.json') or {}).get('complete')),
        'summary':project_summary(root,state.model_dump(mode='json') if state else {},job),
        'updated_at':max((p.stat().st_mtime for p in root.glob('*.json')),default=0)}

def discover(store,workspace):
    directory=Path(workspace)/'poc-projects'
    if directory.exists():
        for root in directory.iterdir():
            if root.is_dir() and (root/'source.json').is_file():
                try:store.register(root)
                except (ValueError,OSError):pass
