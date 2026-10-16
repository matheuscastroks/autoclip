import pytest
from pathlib import Path

def test_settings_includes_openrouter_defaults(tmp_path, monkeypatch):
    from engine.api.settings import Settings
    from engine.adapters.openrouter import credentials
    
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    monkeypatch.setattr(credentials.keyring, 'get_password', lambda *a: None)
    
    settings = Settings(tmp_path)
    cfg = settings.get()
    
    assert cfg['ai_provider'] == 'gemini'
    assert cfg['openrouter_model'] == 'openrouter/free'
    assert cfg['openrouter_key_configured'] is False

def test_settings_saves_openrouter_provider_and_model(tmp_path, monkeypatch):
    from engine.api.settings import Settings
    from engine.adapters.openrouter import credentials
    
    monkeypatch.setattr(credentials, 'get_openrouter_key', lambda: 'sk-or-v1-secret')
    
    settings = Settings(tmp_path)
    updated = settings.save({
        **settings.get(),
        'ai_provider': 'openrouter',
        'openrouter_model': 'meta-llama/llama-3.3-70b-instruct:free'
    })
    
    assert updated['ai_provider'] == 'openrouter'
    assert updated['openrouter_model'] == 'meta-llama/llama-3.3-70b-instruct:free'
    assert updated['openrouter_key_configured'] is True

def test_settings_recovers_provisioned_tools_and_models_when_saved_paths_are_missing(tmp_path, monkeypatch):
    import engine.api.settings as settings_mod
    from engine.api.settings import Settings
    from engine.pipeline.artifacts import atomic_json

    storage = tmp_path / 'appdata'
    model_dir = storage / 'models' / 'whisper-small'
    model_dir.mkdir(parents=True)
    (model_dir / 'model.bin').write_bytes(b'weights')
    bin_dir = storage / 'bin'
    bin_dir.mkdir(parents=True)
    ffmpeg = bin_dir / 'ffmpeg.exe'
    ffprobe = bin_dir / 'ffprobe.exe'
    ffmpeg.write_bytes(b'exe')
    ffprobe.write_bytes(b'exe')

    monkeypatch.setattr(settings_mod, 'locate_tools', lambda: (ffmpeg, ffprobe))
    monkeypatch.setattr('engine.system.provisioner.get_storage_base', lambda: storage)

    workspace = tmp_path / 'workspace'
    # Simulate settings saved before tools/model were provisioned
    atomic_json(workspace / '.autoclip/settings.json', {
        'ffmpeg': '',
        'ffprobe': '.',
        'asr_model_path': str(workspace / 'research/models/whisper-small'),
        'clip_policy_version': 2,
    })

    cfg = Settings(workspace).get()
    assert cfg['tools_available'] is True
    assert cfg['ffmpeg'] == str(ffmpeg)
    assert cfg['ffprobe'] == str(ffprobe)
    assert cfg['asr_available'] is True
    assert cfg['asr_model_path'] == str(model_dir)

