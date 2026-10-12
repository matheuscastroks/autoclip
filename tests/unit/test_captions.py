from test_gemini import transcript,payload
def test_caption_edit_does_not_mutate_raw_asr(tmp_path):
    from engine.contracts import Source,Candidate,CaptionRevision,CaptionConfig
    from engine.editorial.edl import plan_continuous_edit
    from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder
    t=transcript();s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'s.mp4',duration_us=40_000_000)
    e=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s)
    revision=CaptionRevision(edits={'w0':r'Não {texto}\N injetado'})
    caps=OpenShortsCaptionBuilder(tmp_path).build(t,e,revision,CaptionConfig())
    assert t.words[0].text=='Não'
    assert caps.words[0].display_text==revision.edits['w0']
    assert caps.ass_path.exists() and caps.srt_path.exists()
    assert r'{texto}' not in caps.ass_path.read_text(encoding='utf-8')
    assert all(w.end_us<=e.duration_us for w in caps.words)
