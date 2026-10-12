from pathlib import Path
from uuid import UUID
from fastapi import HTTPException
from engine.contracts import *
from engine.pipeline.artifacts import atomic_json
from engine.editorial.review import review_fingerprint,record_review
from engine.pipeline.runner import export_approved
from .projects import read_json

def revision_folder(root,revision):
    try:name=str(UUID(revision))
    except ValueError:raise HTTPException(404,'Corte não encontrado.')
    path=(Path(root)/'revisions'/name).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_dir():raise HTTPException(404,'Corte não encontrado.')
    return path

def list_revisions(root:Path):
    state=read_json(root/'project.json',{}) or {};result=[]
    if (root/'manual-check.json').exists():return []
    for row in state.get('revisions',[]):
        rid=row.get('revision_id','')
        try:
            folder=revision_folder(root,rid)
            edl=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes())
            qa=ExportValidation.model_validate_json((folder/'qa.json').read_bytes())
            candidate=Candidate.model_validate_json((folder/'candidate.json').read_bytes())
            caps=CaptionArtifact.model_validate_json((folder/'captions.json').read_bytes())
            for path in (caps.ass_path,caps.srt_path):
                if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Caption outside project')
            decision=read_json(folder/'review.json',{}) or {};fingerprint=review_fingerprint(root,edl.revision_id)
            status=decision.get('decision','needs_review')
            if status=='approved' and decision.get('content_hash')!=fingerprint:status='stale_review'
            result.append({'revision_id':rid,'title':candidate.title_suggestion or 'Corte para revisar','rationale':candidate.rationale,
                'technical_pass':qa.technical_pass,'review_status':status,'duration_us':edl.duration_us,'start_us':edl.spans[0].source_start_us,
                'end_us':edl.spans[-1].source_end_us,'caption_words':[w.model_dump(mode='json') for w in caps.words],
                'warnings':qa.warnings,'content_hash':fingerprint,'notes':decision.get('notes','')})
        except (OSError,ValueError,PipelineError,HTTPException):
            result.append({'revision_id':rid,'title':'Corte indisponível','technical_pass':False,'review_status':'invalid','warnings':['Artefatos inválidos ou incompletos. Gere a prévia novamente.']})
    return result

def decide(root,revision,decision,checks,notes,content_hash):
    root=Path(root);folder=revision_folder(root,revision)
    available=next((r for r in list_revisions(root) if r['revision_id']==revision),None)
    if not available or not available['technical_pass']:raise HTTPException(400,'A prévia precisa passar pela verificação técnica.')
    fingerprint=review_fingerprint(root,UUID(revision))
    if fingerprint!=content_hash:raise HTTPException(409,'O conteúdo mudou. Reabra e revise a prévia atual.')
    record=record_review(UUID(revision),decision,checks,notes,fingerprint)
    atomic_json(folder/'review.json',record)
    state=ProjectRun.model_validate_json((root/'project.json').read_bytes())
    for row in state.revisions:
        if row.get('revision_id')==revision:row['review_status']=decision
    atomic_json(root/'project.json',state)
    return record.model_dump(mode='json')

def export(root):
    if not (Path(root)/'project.json').is_file():raise HTTPException(400,'Nenhum corte aprovado para exportar.')
    packages=export_approved(root)
    if not packages:raise HTTPException(400,'Revise e aprove pelo menos um corte antes de exportar.')
    return {'paths':packages}
