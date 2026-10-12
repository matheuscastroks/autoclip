from pathlib import Path
from engine.contracts import TranscriptArtifact,EDLArtifact,CaptionRevision,CaptionConfig,CaptionArtifact,CaptionWord,PipelineError
from engine.editorial.edl import output_at
from vendor.openshorts.subtitles import generate_ass_from_captions,generate_srt_from_captions

class OpenShortsCaptionBuilder:
    def __init__(self,root:Path): self.root=Path(root)

    def build(self,transcript:TranscriptArtifact,edl:EDLArtifact,revision:CaptionRevision,config:CaptionConfig) -> CaptionArtifact:
        if transcript.transcript_id!=edl.transcript_id: raise PipelineError('UNSAFE_EDIT','captions','Transcript revision mismatch.')
        ws={w.id:w for w in transcript.words}
        if not set(revision.edits).issubset(ws): raise PipelineError('INVALID_CAPTION','captions','Unknown edited word ID.')
        words=[]
        for wid in edl.protected_word_ids:
            if wid not in ws: raise PipelineError('UNSAFE_EDIT','captions','Protected word missing.')
            w=ws[wid]
            span=next((s for s in edl.spans if s.source_start_us<=w.start_us and w.end_us<=s.source_end_us),None)
            if span is None: raise PipelineError('UNSAFE_EDIT','captions','Protected word is cut.')
            text=revision.edits.get(wid,w.text).strip()
            if not text: raise PipelineError('INVALID_CAPTION','captions','Empty display text must be reviewed explicitly.')
            words.append(CaptionWord(source_word_id=wid,display_text=text,start_us=span.output_start_us+w.start_us-span.source_start_us,end_us=span.output_start_us+w.end_us-span.source_start_us))
        folder=self.root/str(edl.revision_id)/str(revision.revision_id);folder.mkdir(parents=True,exist_ok=False)
        ass,srt=folder/'captions.ass',folder/'captions.srt'
        # Upstream consumes milliseconds; contract retains original microseconds.
        payload=[{'text':w.display_text,'startMs':w.start_us//1000,'endMs':w.end_us//1000} for w in words]
        if not payload: raise PipelineError('INVALID_CAPTION','captions','No caption words.')
        generate_ass_from_captions(payload,str(ass),max_chars=32,max_duration=2.0,font_name=config.font_name,fontsize=22,effect='pop')
        generate_srt_from_captions(payload,str(srt),max_chars=32,max_duration=2.0)
        return CaptionArtifact(transcript_id=transcript.transcript_id,edl_revision_id=edl.revision_id,revision_id=revision.revision_id,words=words,ass_path=ass.resolve(),srt_path=srt.resolve(),font=str(config.font_path) if config.font_path else config.font_name)
