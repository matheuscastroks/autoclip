from pathlib import Path
from uuid import UUID
from fastapi import HTTPException
from engine.contracts import *
from engine.pipeline.artifacts import atomic_json,object_hash
from engine.editorial.review import review_fingerprint,record_review,current_review
from engine.pipeline.runner import export_approved
from .projects import read_json
from engine.editorial.social_copy import publication_description

def revision_folder(root,revision):
    try:name=str(UUID(revision))
    except ValueError:raise HTTPException(404,'Corte não encontrado.')
    path=(Path(root)/'revisions'/name).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_dir():raise HTTPException(404,'Corte não encontrado.')
    return path

def preview_version(root,folder,rid):
    path=folder/'preview.json'
    if not path.exists():return {'state':'not_generated'}
    try:
        value=PreviewArtifact.model_validate_json(path.read_bytes())
        from .media import asset_path
        asset_path(root,'preview-'+rid)
        return {'state':'available','asset':'preview-'+rid,'profile':value.profile,'sha256':value.render.sha256,'duration_us':value.duration_us}
    except (OSError,ValueError,PipelineError,HTTPException):
        return {'state':'invalid','message':'Prévia rápida inválida ou indisponível. Gere novamente.'}


def list_revisions(root:Path):
    root=Path(root).resolve()
    state=read_json(root/'project.json',{}) or {};result=[]
    if (root/'manual-check.json').exists():return []
    for row in state.get('revisions',[]):
        rid=row.get('revision_id','')
        folder=None
        try:
            folder=revision_folder(root,rid)
            if (folder/'deleted.json').is_file():continue
            edl=EDLArtifact.model_validate_json((folder/'edl.json').read_bytes())
            candidate=Candidate.model_validate_json((folder/'candidate.json').read_bytes())
            caps=CaptionArtifact.model_validate_json((folder/'captions.json').read_bytes())
            for path in (caps.ass_path,caps.srt_path):
                if not path.resolve().is_relative_to(root):raise ValueError('Caption outside project')
            preview=preview_version(root,folder,rid)
            prepared=read_json(folder/'prepared.json',{}) or {}
            can_render_final=False
            try:
                from engine.pipeline.outputs import load_preparation
                load_preparation(root,rid,verify_source=False)
                can_render_final=preview['state']=='available'
            except (PipelineError,OSError,ValueError):pass
            final_state='not_generated';technical=False;status='needs_review';decision=None;fingerprint=None;exported=False;warnings=list(edl.warnings)+list(candidate.warnings)
            if (folder/'render.json').exists() or (folder/'qa.json').exists():
                final_state='invalid';status='invalid'
                try:
                    qa=ExportValidation.model_validate_json((folder/'qa.json').read_bytes())
                    rendered=RenderArtifact.model_validate_json((folder/'render.json').read_bytes())
                    from engine.pipeline.artifacts import file_hash
                    if not rendered.path.resolve().is_relative_to(root) or rendered.revision_id!=edl.revision_id or file_hash(rendered.path)!=rendered.sha256:raise ValueError('Invalid final bytes')
                    technical=qa.technical_pass and qa.revision_id==edl.revision_id
                    final_state='available' if technical else 'invalid'
                    fingerprint=review_fingerprint(root,edl.revision_id)
                    status,decision=current_review(folder,edl.revision_id,fingerprint,technical)
                    warnings+=qa.warnings
                    package_hash=object_hash({'review':decision,'edl':edl,'caption':caps,'render':rendered}) if status=='approved' else None
                    manifest=read_json(root/'exports'/rid/package_hash[:16]/'manifest.json') if package_hash else None
                    exported=bool(manifest and manifest.get('package_hash')==package_hash)
                except (OSError,ValueError,PipelineError):warnings.append('Versão final inválida ou incompleta; a prévia existente foi preservada.')
            result.append({'revision_id':rid,'candidate_id':str(candidate.id),'exported':exported,'title':candidate.title_suggestion or 'Corte','rationale':candidate.rationale,'description':publication_description(candidate.description_suggestion,candidate.title_suggestion),'opening_text':caps.opening_text,'opening_duration_us':caps.opening_duration_us,
                'technical_pass':technical,'review_status':status,'duration_us':edl.duration_us,'start_us':edl.spans[0].source_start_us,
                'end_us':edl.spans[-1].source_end_us,'caption_words':[w.model_dump(mode='json') for w in caps.words],
                'playback_speed':getattr(edl,'playback_speed','1x'),'preset_id':getattr(caps,'style_id','karaoke_yellow'),'style_id':getattr(caps,'style_id','karaoke_yellow'),
                'warnings':warnings,'content_hash':fingerprint,'notes':decision.notes if decision else '',
                'removed_silence_us':sum(r['source_end_us']-r['source_start_us'] for r in edl.removed),
                'pause_removals':edl.removed,'preview':preview,'final_state':final_state,
                'can_render_final':can_render_final,'analysis_hash':prepared.get('analysis_hash'),'plan_hash':prepared.get('plan_hash')})

        except (OSError,ValueError,PipelineError,HTTPException):
            preview=preview_version(root,folder,rid) if folder else {'state':'invalid'}
            result.append({'revision_id':rid,'title':'Corte com preparação indisponível','technical_pass':False,'review_status':'invalid','warnings':['A preparação está inválida ou incompleta. A prévia preservada pode ser reproduzida, mas não gerar ou aprovar um final.'],'final_state':'invalid','preview':preview,'can_render_final':False,'duration_us':preview.get('duration_us')})
    return result


def list_deleted(root):
    result=[]
    directory=root/'revisions'
    for path in directory.iterdir() if directory.is_dir() else []:
        try:folder=revision_folder(root,path.name)
        except HTTPException:continue
        if (folder/'deleted.json').is_file():result.append({'revision_id':folder.name,'title':(read_json(folder/'candidate.json',{}) or {}).get('title_suggestion') or 'Corte excluído'})
    return result

def set_deleted(root,revision,deleted):
    folder=revision_folder(root,revision)
    state=read_json(root/'project.json',{}) or {}
    row=next((r for r in state.get('revisions',[]) if r.get('revision_id')==revision),None)
    if deleted:
        if row is None:raise HTTPException(404,'Corte não encontrado.')
        from .store import now
        atomic_json(folder/'deleted.json',{'deleted_at':now(),'revision':row})
    else:
        if row is None:
            stored=(read_json(folder/'deleted.json',{}) or {}).get('revision')
            if not stored or stored.get('revision_id')!=revision:raise HTTPException(409,'Os dados desta revisão não estão disponíveis para restauração.')
            state.setdefault('revisions',[]).append(stored);atomic_json(root/'project.json',state)
        (folder/'deleted.json').unlink(missing_ok=True)
    return {'deleted':deleted}

def decide(root,revision,decision,checks,notes,content_hash):
    root=Path(root);folder=revision_folder(root,revision)
    available=next((r for r in list_revisions(root) if r['revision_id']==revision),None)
    if not available or not available['technical_pass']:raise HTTPException(400,'A prévia precisa passar pela verificação técnica.')
    fingerprint=review_fingerprint(root,UUID(revision))
    if fingerprint!=content_hash:raise HTTPException(409,'O conteúdo mudou. Reabra e revise a prévia atual.')
    record=record_review(UUID(revision),decision,checks,notes,fingerprint)
    atomic_json(folder/'review.json',record)
    # The worker owns the revision index. Decisions are authoritative in review.json;
    # writing that index here would race previews published during a batch.
    return record.model_dump(mode='json')

def export(root):
    if not (Path(root)/'project.json').is_file():raise HTTPException(400,'Nenhum corte pronto para exportar.')
    packages=export_approved(root)
    if not packages:raise HTTPException(400,'Aprove editorialmente pelo menos um corte antes de exportar.')
    return {'paths':packages}
