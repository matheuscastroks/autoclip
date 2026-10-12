"""Reproducible, allowlisted MIT snapshot vendoring, no network or execution."""
import hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root/'research/snapshots/Marsic1__openshorts/source'
dest = root/'vendor/openshorts'
dest.mkdir(parents=True, exist_ok=True)
(root/'vendor/__init__.py').write_text('', encoding='utf-8')
(dest/'__init__.py').write_text('', encoding='utf-8')
rows = []
for name in ['clip_selection.py','transcribe_backends.py','subtitles.py','ffmpeg_utils.py','recut.py','LICENSE']:
    original = (source/name).read_bytes()
    text = original.decode('utf-8')
    for module in ['subtitles','ffmpeg_utils','clip_selection','transcribe_backends']:
        text = text.replace(f'from {module} import', f'from .{module} import')
    if name == 'subtitles.py':
        text = text.replace("if cur_len + len(w['word']) > max_chars or dur > max_duration:", "if len(current) >= 4 or cur_len + len(w['word']) > max_chars or dur > max_duration:")
    if name == 'recut.py':
        # Keep only pure timeline functions. Render functions pull in main.py.
        text = text[:text.index('\ndef cut_commands(')]
    if name == 'transcribe_backends.py':
        # Retain upstream structure, but expose explicit isolated-model helper.
        text += '\n\ndef transcribe_explicit(media_path, model, language="pt"):\n    segments, info = model.transcribe(media_path, **dict(WHISPER_TRANSCRIBE_PARAMS, language=language))\n    result = []\n    for segment in segments:\n        words = merge_continuation_words([{\"word\": w.word, \"start\": float(w.start), \"end\": float(w.end), \"probability\": getattr(w, \"probability\", None)} for w in (segment.words or [])])\n        result.append({\"start\": float(segment.start), \"end\": float(segment.end), \"text\": segment.text, \"words\": words})\n    return {\"text\": \" \".join(s[\"text\"].strip() for s in result), \"language\": info.language, \"segments\": result}\n'
    (dest/name).write_text(text, encoding='utf-8')
    rows.append({'file': name, 'original_sha256': hashlib.sha256(original).hexdigest(), 'vendored_sha256': hashlib.sha256((dest/name).read_bytes()).hexdigest()})
(dest/'UPSTREAM.json').write_text(json.dumps({'repository': 'https://github.com/Marsic1/openshorts', 'commit': 'b1f5350fcf24b17cb48b581400c35ad9f3974ba5', 'license': 'MIT (outside cloud/)', 'changes': ['relative imports', 'recut render wrappers excluded', 'explicit per-job Whisper helper', 'caption groups limited to four words'], 'files': rows}, indent=2), encoding='utf-8')
print('Vendored allowlisted MIT source files; cloud excluded.')
