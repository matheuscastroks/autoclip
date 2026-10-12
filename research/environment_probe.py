"""Record benchmark prerequisites without modifying global configuration."""
import importlib.util, json, os, pathlib, platform, shutil, subprocess, urllib.request

root = pathlib.Path(__file__).parent
ffmpeg = pathlib.Path('C:/Users/Matheus/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe')
result = {'python': platform.python_version(), 'os': platform.platform(), 'cpu_count': os.cpu_count(), 'tools': {name: shutil.which(name) for name in ['ffmpeg', 'ffprobe', 'ollama', 'nim', 'node', 'whisper-cli']}, 'modules': {name: importlib.util.find_spec(name) is not None for name in ['pytest', 'numpy', 'cv2', 'faster_whisper', 'mediapipe', 'pydantic', 'httpx']}}
if ffmpeg.exists():
    result['ffmpeg_path'] = str(ffmpeg)
    result['ffmpeg_version'] = subprocess.run([str(ffmpeg), '-version'], capture_output=True, text=True).stdout
try:
    result['ollama'] = json.loads(urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3).read())
except Exception as exc:
    result['ollama'] = {'error': str(exc)}
(root / 'environment.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
