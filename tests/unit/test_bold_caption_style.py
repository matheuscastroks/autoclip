import re
from test_gemini import transcript,payload
from engine.contracts import Source,Candidate,CaptionConfig,CaptionRevision
from engine.editorial.edl import plan_continuous_edit
from engine.adapters.openshorts.captions import OpenShortsCaptionBuilder

def test_bold_uppercase_three_word_karaoke_keeps_source_intact(tmp_path):
    t=transcript();original=[w.model_dump() for w in t.words]
    s=Source(id=t.source_id,sha256=t.source_sha256,local_path=tmp_path/'s.mp4',duration_us=40_000_000)
    edl=plan_continuous_edit(Candidate.model_validate(payload(t)['candidates'][0]),t,s)
    caps=OpenShortsCaptionBuilder(tmp_path).build(t,edl,CaptionRevision(),CaptionConfig())
    ass=caps.ass_path.read_text(encoding='utf-8');srt=caps.srt_path.read_text(encoding='utf-8-sig')
    assert 'Montserrat ExtraBold' in ass and r'\c&H00CCFF&' in ass
    style=next(line for line in ass.splitlines() if line.startswith('Style:')).split(',')
    assert style[3]=='&H00FFFFFF' and style[5]=='&H00000000' and float(style[16])>=3
    for line in ass.splitlines():
        if not line.startswith('Dialogue:'):continue
        visible=re.sub(r'\{[^}]*\}','',line.split(',',9)[9]).replace(r'\N',' ')
        assert 1<=len(visible.split())<=3 and visible==visible.upper()
        assert line.count(r'\c&H00CCFF&')==1
    for block in srt.strip().split('\n\n'):
        text=' '.join(block.splitlines()[2:]);assert len(text.split())<=3 and text==text.upper()
    assert [w.model_dump() for w in t.words]==original
    assert [(w.start_us,w.end_us) for w in caps.words]==[(w.start_us,w.end_us) for w in t.words]

def test_overlapping_asr_words_do_not_overlay_caption_groups(tmp_path):
    from vendor.openshorts.subtitles import generate_ass_from_captions
    words=[{'text':'UM','startMs':0,'endMs':1500},{'text':'DOIS','startMs':400,'endMs':900},{'text':'TRÊS','startMs':900,'endMs':1300},{'text':'QUATRO','startMs':1200,'endMs':1600}]
    output=tmp_path/'overlap.ass';generate_ass_from_captions(words,str(output),max_chars=100,max_words=3)
    def seconds(value):
        h,m,s=value.split(':');return int(h)*3600+int(m)*60+float(s)
    rows=[line.split(',',9) for line in output.read_text().splitlines() if line.startswith('Dialogue:')]
    ranges=[(seconds(row[1]),seconds(row[2])) for row in rows]
    assert all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:]))
    assert words[0]['endMs']==1500
