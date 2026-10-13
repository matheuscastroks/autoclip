"""A short editorial headline, independent of word-synchronised speech subtitles."""
import re,textwrap
from pathlib import Path

def normalize_opening(text):
    return ' '.join(re.sub(r'\\[A-Za-z]+(?:\([^)]*\))?',' ',text).replace('{','').replace('}','').split())

def opening_for(candidate):
    text=normalize_opening(candidate.opening_suggestion) or normalize_opening(candidate.title_suggestion)
    return text if len(text)<=100 else ''

def add_opening(path:Path,text:str,duration_us:int,font_name:str):
    # Treat provider text as plain text. No ASS tags, escapes or structural lines.
    text=normalize_opening(text).upper()
    if not text:return
    lines=textwrap.wrap(text,width=25,break_long_words=True,break_on_hyphens=False)
    # At most four lines even for legacy titles; shrink long headlines rather than truncate claims.
    if len(lines)>4:lines=textwrap.wrap(text,width=30,break_long_words=True,break_on_hyphens=False)
    size=10 if max(map(len,lines))<=25 else 9
    safe_font=font_name.replace(',','').replace('\n','').replace('\r','')
    style=f'Style: Opening,{safe_font},{size},&H00FFFFFF,&H00FFFFFF,&H006D2844,&H006D2844,1,0,0,0,100,100,0,0,3,4,0,8,20,20,24,1\n'
    end=f'0:{duration_us//60_000_000:02d}:{duration_us%60_000_000/1e6:05.2f}'
    duration_ms=duration_us//1000
    transition=min(300,duration_ms//3)
    def stamp(ms):return f'0:{ms//60000:02d}:{ms%60000/1000:05.2f}'
    body=r'\N'.join(lines)
    # ASS defaults to a 384 x 288 canvas when PlayResX is omitted.
    events=[(0,transition,rf'{{\move(192,-50,192,24,0,{transition})\fad({transition},0)}}'),(transition,duration_ms-transition,r'{\pos(192,24)}'),(duration_ms-transition,duration_ms,rf'{{\move(192,24,192,-50,0,{transition})\fad(0,{transition})}}')]
    dialogue=''.join(f'Dialogue: 1,{stamp(start)},{stamp(stop)},Opening,,0,0,0,,{tags}{body}\n' for start,stop,tags in events if stop>start)
    contents=path.read_text(encoding='utf-8')
    path.write_text(contents.replace('[Events]',style+'\n[Events]',1)+'\n'+dialogue,encoding='utf-8')
