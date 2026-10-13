import pytest
from engine.contracts import PipelineError

def test_missing_openrouter_key(monkeypatch):
    from engine.adapters.openrouter import credentials
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    monkeypatch.setattr(credentials.keyring, 'get_password', lambda *a: None)
    with pytest.raises(PipelineError) as exc:
        credentials.get_openrouter_key()
    assert exc.value.code == 'PROVIDER_AUTH'

def test_set_and_get_openrouter_key(monkeypatch):
    from engine.adapters.openrouter import credentials
    stored = {}
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    monkeypatch.setattr(credentials.keyring, 'set_password', lambda service, user, secret: stored.update({(service, user): secret}))
    monkeypatch.setattr(credentials.keyring, 'get_password', lambda service, user: stored.get((service, user)))
    
    credentials.set_openrouter_key('sk-or-v1-testkey123')
    assert credentials.get_openrouter_key() == 'sk-or-v1-testkey123'

def test_openrouter_env_key_takes_precedence(monkeypatch):
    from engine.adapters.openrouter import credentials
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-v1-envkey')
    assert credentials.get_openrouter_key() == 'sk-or-v1-envkey'

def test_invalid_key_characters_rejected():
    from engine.adapters.openrouter import credentials
    with pytest.raises(PipelineError):
        credentials.set_openrouter_key('key with spaces')
    with pytest.raises(PipelineError):
        credentials.set_openrouter_key('')
