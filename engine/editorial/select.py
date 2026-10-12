from engine.contracts import AnalysisArtifact,TranscriptArtifact,SelectionConfig,CandidateArtifact,PipelineError


def select_candidates(analysis:AnalysisArtifact,transcript:TranscriptArtifact,config:SelectionConfig) -> CandidateArtifact:
    if not analysis.complete or analysis.transcript_id!=transcript.transcript_id:
        raise PipelineError('INCOMPLETE_ANALYSIS','select','Complete analysis of this transcript is required.')
    ids={w.id:i for i,w in enumerate(transcript.words)};kept=[];ranges=[];rejected=[]
    for candidate in analysis.candidates:
        reason=None
        if candidate.start_word_id not in ids or candidate.end_word_id not in ids: reason='unknown boundary IDs'
        elif not set(candidate.evidence_word_ids+candidate.context_before_word_ids+candidate.context_after_word_ids).issubset(ids): reason='unknown evidence/context IDs'
        else:
            a,b=ids[candidate.start_word_id],ids[candidate.end_word_id]
            if b<a: reason='reversed boundaries'
            elif not all(v=='yes' for v in candidate.editorial.model_dump(exclude={'schema_version'}).values()): reason='editorial flags require review'
            else:
                start,end=transcript.words[a].start_us,transcript.words[b].end_us
                if not config.min_us<=end-start<=config.max_us: reason='duration outside 20–60 seconds'
                elif any(max(0,min(end,y)-max(start,x))/(max(end,y)-min(start,x))>=.5 for x,y in ranges): reason='duplicate overlapping candidate'
                elif len(kept)>=config.max_clips: reason='maximum candidates reached'
                else: kept.append(candidate);ranges.append((start,end))
        if reason: rejected.append({'candidate_id':str(candidate.id),'reason':reason})
    kept.sort(key=lambda c:ids[c.start_word_id])
    return CandidateArtifact(transcript_id=transcript.transcript_id,candidates=kept,rejected=rejected)
