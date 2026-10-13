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
