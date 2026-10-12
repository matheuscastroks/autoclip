"""Read only editorial view, derived from validated artifacts rather than event tails."""
import unicodedata
from pathlib import Path
from engine.contracts import AnalysisArtifact,TranscriptArtifact,SelectionConfig
from engine.editorial.select import select_candidates
from engine.pipeline.artifacts import object_hash,atomic_json
from fastapi import HTTPException
from .projects import read_json
from engine.render.opening import opening_for

def normalized(label):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',label.casefold()) if not unicodedata.combining(c)).split())

def analysis_view(root,job=None,job_folder=None,max_seconds=180):
    root=Path(root);active=job and job['operation'] in ('analyze','prepare') and job['status']!='completed'
    preview=read_json(Path(job_folder)/'analysis-preview.json') if active and job_folder else None
    path=root/'analysis.json';transcript_path=root/'transcript.json'
    empty={'schema_version':'1.0','state':'not_started','job_id':job['id'] if job else None,'analysis_hash':None,'model':None,'completed_windows':0,'total_windows':0,'topic_groups':[],'proposals':[]}
    if not transcript_path.exists():return empty
    t=TranscriptArtifact.model_validate_json(transcript_path.read_bytes())
    if active:
        empty['state']='running' if job['status'] in ('running','pending','cancelling') else job['status'] if job['status'] in ('failed','cancelled') else 'failed'
        if not preview:return empty
        a=AnalysisArtifact.model_validate(preview['analysis'])
        if str(t.transcript_id)!=str(a.transcript_id):return empty
        complete=False;done=preview['completed_windows'];total=preview['total_windows']
    elif path.exists():
        a=AnalysisArtifact.model_validate_json(path.read_bytes());complete=a.complete
        if a.transcript_id!=t.transcript_id or complete and set(a.covered_word_ids)!={w.id for w in t.words}:return empty
        done=total=len(a.responses)
    else:return empty
    words={w.id:w for w in t.words};order={w.id:i for i,w in enumerate(t.words)}
    groups={};topic_group={}
    for topic in a.topics:
        key=normalized(topic.label)
        group=groups.setdefault(key,{'id':key,'label':topic.label,'topic_ids':[],'summaries':[],'evidence_word_ids':[]})
        group['topic_ids'].append(topic.id);topic_group[topic.id]=key
        if topic.summary not in group['summaries']:group['summaries'].append(topic.summary)
        group['evidence_word_ids']=list(dict.fromkeys(group['evidence_word_ids']+topic.evidence_word_ids))
    proposals=[]
    for c in a.candidates:
        if c.start_word_id not in words or c.end_word_id not in words:continue
        begin,end=order[c.start_word_id],order[c.end_word_id]
        if end<begin:continue
        start=words[c.start_word_id].start_us;stop=max(w.end_us for w in t.words[begin:end+1])
        checked=select_candidates(a.model_copy(update={'complete':True,'candidates':[c]}),t,SelectionConfig(min_us=a.clip_min_seconds*1_000_000,max_us=max_seconds*1_000_000))
        translations={'editorial flags require review':'O modelo indicou incerteza sobre integridade ou contexto.','unknown boundary IDs':'Referências de início ou fim inválidas.','unknown evidence/context IDs':'Referências de evidência ou contexto inválidas.','reversed boundaries':'Limites do trecho invertidos.'}
        reasons=[f'Duração fora da faixa de {a.clip_min_seconds} a {max_seconds} segundos.' if r['reason'].startswith('duration outside') else translations.get(r['reason'],r['reason']) for r in checked.rejected]
        proposals.append({'candidate_id':str(c.id),'topic_ids':[c.topic_id],'group_id':topic_group.get(c.topic_id,''),'title':c.title_suggestion or 'Trecho sugerido','opening_text':opening_for(c),'description':c.description_suggestion,'rationale':c.rationale,'start_us':start,'end_us':stop,'duration_us':stop-start,'start_word_id':c.start_word_id,'end_word_id':c.end_word_id,'evidence_word_ids':c.evidence_word_ids,'editorial':c.editorial.model_dump(mode='json'),'warnings':c.warnings,'eligible':not reasons,'reasons':reasons,'text':' '.join(w.text for w in t.words[begin:end+1]),'context_before':' '.join(w.text for w in t.words[max(0,begin-12):begin]),'context_after':' '.join(w.text for w in t.words[end+1:end+13])})
    return {**empty,'state':'completed' if complete else 'partial' if empty['state']=='running' else empty['state'],'analysis_hash':object_hash(a) if complete else None,'model':a.model,'completed_windows':done,'total_windows':total,'topic_groups':list(groups.values()),'proposals':proposals}

def validate_selection(root,analysis_hash,candidate_ids,max_seconds=180):
    view=analysis_view(root,max_seconds=max_seconds)
    if view['state']!='completed' or view['analysis_hash']!=analysis_hash:raise HTTPException(409,'A análise mudou. Reabra as propostas antes de gerar.')
    if len(candidate_ids)>10 and AnalysisArtifact.model_validate_json((Path(root)/'analysis.json').read_bytes()).clip_min_seconds>=60:raise HTTPException(422,'Selecione no máximo 10 cortes.')
    eligible={c['candidate_id'] for c in view['proposals'] if c['eligible']}
    if len(candidate_ids)!=len(set(candidate_ids)) or not set(candidate_ids)<=eligible:raise HTTPException(422,'Seleção inválida ou com trechos que precisam de atenção.')
    value={'schema_version':'1.0','analysis_hash':analysis_hash,'candidate_ids':candidate_ids}
    return value

def save_selection(root,analysis_hash,candidate_ids,max_seconds=180):
    value=validate_selection(root,analysis_hash,candidate_ids,max_seconds)
    atomic_json(Path(root)/'analysis-selection.json',value)
    return value
