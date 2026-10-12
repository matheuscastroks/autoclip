from engine.contracts import Candidate,TranscriptArtifact,Source,EDLArtifact,Span,PipelineError
from vendor.openshorts.recut import normalize_segments


def plan_continuous_edit(candidate:Candidate,transcript:TranscriptArtifact,source:Source) -> EDLArtifact:
    if transcript.source_id!=source.id or transcript.source_sha256!=source.sha256:
        raise PipelineError('SOURCE_CHANGED','edit_plan','Transcript does not match source.')
    ids={w.id:i for i,w in enumerate(transcript.words)}
    if candidate.start_word_id not in ids or candidate.end_word_id not in ids:
        raise PipelineError('UNSAFE_EDIT','edit_plan','Unknown boundary word.')
    a,b=ids[candidate.start_word_id],ids[candidate.end_word_id]
    if b<a: raise PipelineError('UNSAFE_EDIT','edit_plan','Reversed boundaries.')
    selected=transcript.words[a:b+1]
    start,end=selected[0].start_us,max(w.end_us for w in selected)
    if not 20_000_000<=end-start<=60_000_000:
        raise PipelineError('UNSAFE_EDIT','edit_plan','Complete words do not fit 20–60 seconds.')
    previous_end=max((w.end_us for w in transcript.words[:a]),default=0)
    next_start=min((w.start_us for w in transcript.words[b+1:]),default=source.duration_us)
    if previous_end>start or next_start<end:
        raise PipelineError('UNSAFE_EDIT','edit_plan','Boundary overlaps other speech; review required.')
    padding_budget=60_000_000-(end-start)
    lead=min(150_000,start-previous_end,padding_budget//2)
    tail=min(150_000,next_start-end,padding_budget-lead)
    start-=max(0,lead);end+=max(0,tail)
    if end>source.duration_us: raise PipelineError('UNSAFE_EDIT','edit_plan','Word exceeds source duration.')
    # Keep upstream range validation, while canonical integer timing stays exact.
    normalize_segments([{'start':start/1e6,'end':end/1e6}],source.duration_us/1e6)
    return EDLArtifact(source_id=source.id,transcript_id=transcript.transcript_id,spans=[Span(source_start_us=start,source_end_us=end,output_start_us=0,output_end_us=end-start)],duration_us=end-start,protected_word_ids=[w.id for w in selected])

def source_at(edl:EDLArtifact,output_us:int) -> int | None:
    for span in edl.spans:
        if span.output_start_us<=output_us<span.output_end_us: return span.source_start_us+output_us-span.output_start_us
    return None

def output_at(edl:EDLArtifact,source_us:int) -> int | None:
    for span in edl.spans:
        if span.source_start_us<=source_us<span.source_end_us: return span.output_start_us+source_us-span.source_start_us
    return None
