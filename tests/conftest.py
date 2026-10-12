import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FFBIN = pathlib.Path('C:/Users/Matheus/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin')

@pytest.fixture
def ffmpeg():
    if not (FFBIN/'ffmpeg.exe').exists(): pytest.skip('FFmpeg unavailable')
    return FFBIN/'ffmpeg.exe'

@pytest.fixture
def ffprobe(): return FFBIN/'ffprobe.exe'

@pytest.fixture
def real_source(): return ROOT/'research/media/z0cf-eWBVCo.mp4'
