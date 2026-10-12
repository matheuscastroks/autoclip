from engine.contracts import Candidate,TranscriptArtifact,Source,EDLArtifact,Span,PipelineError,SelectionConfig,PauseConfig
from vendor.openshorts.recut import normalize_segments


def plan_continuous_edit(candidate:Candidate,transcript:TranscriptArtifact,source:Source,*,selection=None,pauses=None,verified_silences=None) -> EDLArtifact:
    selection=selection or SelectionConfig();pauses=pauses or PauseConfig()
    if transcript.source_id!=source.id or transcript.source_sha256!=source.sha256:
        raise PipelineError('SOURCE_CHANGED','edit_plan','Transcript does not match source.')
    ids={w.id:i for i,w in enumerate(transcript.words)}
    if candidate.start_word_id not in ids or candidate.end_word_id not in ids:
        raise PipelineError('UNSAFE_EDIT','edit_plan','Unknown boundary word.')
    a,b=ids[candidate.start_word_id],ids[candidate.end_word_id]
    if b<a: raise PipelineError('UNSAFE_EDIT','edit_plan','Reversed boundaries.')
    selected=transcript.words[a:b+1]
    start,end=selected[0].start_us,max(w.end_us for w in selected)
    if not selection.min_us<=end-start<=selection.max_us:
        raise PipelineError('UNSAFE_EDIT','edit_plan','Complete words do not fit the configured duration range.')
    previous_end=max((w.end_us for w in transcript.words[:a]),default=0)
    next_start=min((w.start_us for w in transcript.words[b+1:]),default=source.duration_us)
    if previous_end>start or next_start<end:
        raise PipelineError('UNSAFE_EDIT','edit_plan','Boundary overlaps other speech; review required.')
    padding_budget=selection.max_us-(end-start)
    lead=min(150_000,start-previous_end,padding_budget//2)
    tail=min(150_000,next_start-end,padding_budget-lead)
    start-=max(0,lead);end+=max(0,tail)
    if end>source.duration_us: raise PipelineError('UNSAFE_EDIT','edit_plan','Word exceeds source duration.')
    # Keep upstream range validation, while canonical integer timing stays exact.
    normalize_segments([{'start':start/1e6,'end':end/1e6}],source.duration_us/1e6)
    removed=[];warnings=[]
    if pauses.enabled:
        if verified_silences is None:warnings.append('Pausas preservadas: não houve confirmação no áudio.')
        elif verified_silences.source_id!=source.id or verified_silences.source_sha256!=source.sha256:raise PipelineError('SOURCE_CHANGED','edit_plan','Pause verification belongs to another source.')
        else:
            warnings.extend(verified_silences.warnings)
            # Every removal stays between complete words, inside verified quiet
            # nonspeech, with breath/boundary padding retained on both sides.
            for i,right in enumerate(selected[1:],1):
                left_end=max(w.end_us for w in selected[:i])
                gap_start=left_end+pauses.margin_us;gap_end=right.start_us-pauses.margin_us
                for silence in verified_silences.silences:
                    a=max(gap_start,silence.start_us);b=min(gap_end,silence.end_us)
                    if b-a<pauses.min_pause_us:continue
                    keep=pauses.keep_pause_us//2
                    removed.append({'source_start_us':a+keep,'source_end_us':b-keep,'reason':'verified_quiet_nonspeech','method':verified_silences.method})
    removed.sort(key=lambda r:r['source_start_us'])
    spans=[];cursor=start;output=0
    for cut in removed:
        if cut['source_start_us']<cursor:raise PipelineError('UNSAFE_EDIT','edit_plan','Overlapping pause removal.')
        length=cut['source_start_us']-cursor
        if length:spans.append(Span(source_start_us=cursor,source_end_us=cut['source_start_us'],output_start_us=output,output_end_us=output+length));output+=length
        cursor=cut['source_end_us']
    if end>cursor:spans.append(Span(source_start_us=cursor,source_end_us=end,output_start_us=output,output_end_us=output+end-cursor));output+=end-cursor
    if any(not any(s.source_start_us<=w.start_us and w.end_us<=s.source_end_us for s in spans) for w in selected):raise PipelineError('UNSAFE_EDIT','edit_plan','Pause removal intersects a protected word.')
    return EDLArtifact(source_id=source.id,transcript_id=transcript.transcript_id,spans=spans,removed=removed,duration_us=output,protected_word_ids=[w.id for w in selected],warnings=warnings)

def source_at(edl:EDLArtifact,output_us:int) -> int | None:
    for span in edl.spans:
        if span.output_start_us<=output_us<span.output_end_us: return span.source_start_us+output_us-span.output_start_us
    return None

def output_at(edl:EDLArtifact,source_us:int) -> int | None:
    for span in edl.spans:
        if span.source_start_us<=source_us<span.source_end_us: return span.output_start_us+source_us-span.source_start_us
    return None
