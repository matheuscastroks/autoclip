import pytest
from engine.pipeline.fingerprints import ROOT, safe_file_hash


@pytest.mark.parametrize('path, expected', [
    ('engine/media/audio.py', 'cc6a07199dcb8055a853a6f44eee688cfdf6223fb9fe09565ba99f1ce33a316d'),
    ('engine/worker.py', 'bb668ee28c693a3d870e09d5e13cb9e365ab481de1939d4f5262050afa04c356'),
    ('engine/adapters/openshorts/transcriber.py', '94d79fe3ce8e3eed4cb4ba67f1970ed353768144776ecd3a4d9746e7fcc4e477'),
    ('engine/render/verify.py', '67b0779af0fddd4771536292e049adb2068d2ca6aa97119a96a415dcccc25ba5'),
])
def test_reviewed_telemetry_only_changes_keep_existing_cache_identity(path, expected):
    assert safe_file_hash(ROOT / path) == expected


def test_unrecognized_content_never_gets_a_legacy_identity():
    from engine.pipeline.fingerprints import media_code_hash
    assert media_code_hash('engine/media/audio.py', 'f' * 64) == 'f' * 64
