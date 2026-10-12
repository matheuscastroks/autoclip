"""Download the user-selected common benchmark source; no browser cookies."""
import json, pathlib, sys, traceback

root = pathlib.Path(__file__).parent
sys.path.insert(0, str(root / 'tools'))
import yt_dlp

media = root / 'media'
media.mkdir(exist_ok=True)
url = 'https://www.youtube.com/watch?v=z0cf-eWBVCo'
options = {'format': 'bv*[height<=720]+ba/best', 'outtmpl': str(media / '%(id)s.%(ext)s'), 'writeinfojson': True, 'noplaylist': True, 'socket_timeout': 20, 'retries': 1, 'js_runtimes': {'node': {'path': 'C:/Program Files/nodejs/node.exe'}}, 'ffmpeg_location': 'C:/Users/Matheus/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin', 'merge_output_format': 'mp4'}
result = {'url': url, 'yt_dlp_version': yt_dlp.version.__version__, 'status': 'failed'}
try:
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        file = pathlib.Path(downloader.prepare_filename(info))
        result.update(status='downloaded', path=str(file), size=file.stat().st_size, title=info['title'], duration=info.get('duration'), channel=info.get('channel'))
except Exception as exc:
    result['error'] = str(exc)
    traceback.print_exc()
(root / 'download-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
sys.exit(0 if result['status'] == 'downloaded' else 1)
