from engine.contracts import TranscriptArtifact
from vendor.openshorts.clip_selection import build_transcript_windows


def build_windows(transcript:TranscriptArtifact,window_seconds=180,max_text_chars=12000) -> list[dict]:
    segments=transcript.segments
    raw={'segments':[{'start':s.start_us/1e6,'end':s.end_us/1e6,'text':s.text} for s in segments]}
    if not segments:
        raw={'segments':[{'start':w.start_us/1e6,'end':w.end_us/1e6,'text':w.text} for w in transcript.words]}
    windows=build_transcript_windows(raw,transcript.words[-1].end_us/1e6,window_seconds=window_seconds,overlap_seconds=30)
    result=[];seen=set()
    for base in windows:
        ws=[w for w in transcript.words if w.start_us < round(base['end']*1e6) and w.end_us > round(base['start']*1e6)]
        i=0
        while i<len(ws):
            j=i;length=0
            while j<len(ws):
                extra=len(ws[j].text)+len(ws[j].id)+4
                if j>i and (length+extra>max_text_chars or ws[j].end_us-ws[i].start_us>window_seconds*1_000_000): break
                length+=extra;j+=1
            chunk=ws[i:j]
            key=(chunk[0].id,chunk[-1].id)
            if key not in seen:
                seen.add(key);result.append({'id':f'window_{len(result):04d}','words':chunk,'text':' '.join(f'[{w.id}] {w.text}' for w in chunk)})
            if j==len(ws): break
            target=chunk[-1].end_us-30_000_000
            i=next((k for k in range(i+1,j) if ws[k].start_us>=target),j)
    return result
