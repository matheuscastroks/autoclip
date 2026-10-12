"""Fingerprint and decode common media for research, not a product pipeline."""
import hashlib, json, pathlib, subprocess

root = pathlib.Path(__file__).parent
media = root / 'media/z0cf-eWBVCo.mp4'
ffbin = pathlib.Path('C:/Users/Matheus/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin')
out = root / 'results'
out.mkdir(exist_ok=True)
probe = subprocess.run([str(ffbin / 'ffprobe.exe'), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(media)], capture_output=True, text=True, check=True)
metadata = json.loads(probe.stdout)
digest = hashlib.file_digest(media.open('rb'), 'sha256').hexdigest()
manifest = {'video_id': 'z0cf-eWBVCo', 'sha256': digest, 'bytes': media.stat().st_size, 'probe': metadata, 'sample_start_s': 60, 'sample_duration_s': 120, 'reason': 'Fixed reproducible ASR smoke sample; not a full semantic evaluation.'}
(out / 'media-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
subprocess.run([str(ffbin / 'ffmpeg.exe'), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-ss', '60', '-i', str(media), '-t', '120', '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(out / 'common-120s.wav')], check=True)
print(json.dumps({'sha256': digest, 'duration': metadata['format']['duration'], 'audio_bytes': (out / 'common-120s.wav').stat().st_size}))
