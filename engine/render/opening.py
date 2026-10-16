"""A short editorial headline, independent of word-synchronised speech subtitles."""
import re
import textwrap
from pathlib import Path
from engine.render.presets import get_preset


def normalize_opening(text):
    return ' '.join(re.sub(r'\\[A-Za-z]+(?:\([^)]*\))?', ' ', text or '').replace('{', '').replace('}', '').split())


def opening_for(candidate):
    text = normalize_opening(candidate.opening_suggestion) or normalize_opening(candidate.title_suggestion)
    return text if len(text) <= 100 else ''


def add_opening(path: Path, text: str, duration_us: int, font_name: str, preset_id: str | None = None):
    spec = get_preset(preset_id).opening
    # Treat provider text as plain text. No ASS tags, escapes or structural lines.
    clean = normalize_opening(text)
    if not clean:
        return
    formatted = clean.upper() if spec.uppercase else clean
    lines = textwrap.wrap(formatted, width=spec.wrap_width, break_long_words=True, break_on_hyphens=False)
    # At most four lines even for legacy titles; shrink long headlines rather than truncate claims.
    if len(lines) > 4:
        lines = textwrap.wrap(formatted, width=spec.long_wrap_width, break_long_words=True, break_on_hyphens=False)
    size = spec.size if max(map(len, lines)) <= spec.wrap_width else spec.long_size
    safe_font = (font_name or spec.font_name).replace(',', '').replace('\n', '').replace('\r', '')
    style = (
        f'Style: Opening,{safe_font},{size},{spec.primary_colour},{spec.secondary_colour},'
        f'{spec.outline_colour},{spec.back_colour},{spec.bold},0,0,0,100,100,{spec.spacing},0,'
        f'{spec.border_style},{spec.outline},{spec.shadow},{spec.alignment},'
        f'{spec.margin_l},{spec.margin_r},{spec.margin_v},1\n'
    )
    duration_ms = duration_us // 1000
    transition = min(300, duration_ms // 3)

    def stamp(ms):
        return f'0:{ms // 60000:02d}:{ms % 60000 / 1000:05.2f}'

    body = f'{spec.accent_prefix}' + r'\N'.join(lines)
    y = spec.margin_v
    if spec.mode == 'sober_card':
        events = [
            (0, transition, rf'{{\pos(192,{y})\fad({transition},0)}}'),
            (transition, duration_ms - transition, rf'{{\pos(192,{y})}}'),
            (duration_ms - transition, duration_ms, rf'{{\pos(192,{y})\fad(0,{transition})}}'),
        ]
    elif spec.mode == 'documentary_band':
        events = [
            (0, transition, rf'{{\move(176,{y},192,{y},0,{transition})\fad({transition},0)}}'),
            (transition, duration_ms - transition, rf'{{\pos(192,{y})}}'),
            (duration_ms - transition, duration_ms, rf'{{\move(192,{y},208,{y},0,{transition})\fad(0,{transition})}}'),
        ]
    elif spec.mode == 'kinetic_coral':
        events = [
            (0, transition, rf'{{\move(192,8,192,{y},0,{transition})\fscx92\fscy92\t(0,{transition},\fscx100\fscy100)\fad({transition},0)}}'),
            (transition, duration_ms - transition, rf'{{\pos(192,{y})}}'),
            (duration_ms - transition, duration_ms, rf'{{\move(192,{y},192,8,0,{transition})\fad(0,{transition})}}'),
        ]
    else:
        events = [
            (0, transition, rf'{{\move(192,-50,192,{y},0,{transition})\fad({transition},0)}}'),
            (transition, duration_ms - transition, rf'{{\pos(192,{y})}}'),
            (duration_ms - transition, duration_ms, rf'{{\move(192,{y},192,-50,0,{transition})\fad(0,{transition})}}'),
        ]
    dialogue = ''.join(
        f'Dialogue: 1,{stamp(start)},{stamp(stop)},Opening,,0,0,0,,{tags}{body}\n'
        for start, stop, tags in events
        if stop > start
    )
    contents = path.read_text(encoding='utf-8')
    path.write_text(contents.replace('[Events]', style + '\n[Events]', 1) + '\n' + dialogue, encoding='utf-8')
