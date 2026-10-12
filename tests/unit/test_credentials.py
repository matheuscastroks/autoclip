import pytest
def test_missing_key_never_stored_plaintext(monkeypatch):
    from engine.adapters.gemini import credentials
    from engine.contracts import PipelineError
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    monkeypatch.setattr(credentials.keyring,'get_password',lambda *a:None)
    with pytest.raises(PipelineError): credentials.get_gemini_key()
    def fail(*a): raise RuntimeError('backend failure')
    monkeypatch.setattr(credentials.keyring,'set_password',fail)
    with pytest.raises(PipelineError): credentials.set_gemini_key('sentinel-secret')

def test_env_key_is_not_echoed(monkeypatch):
    from engine.adapters.gemini.credentials import get_gemini_key
    monkeypatch.setenv('GEMINI_API_KEY','sentinel-secret')
    assert get_gemini_key()=='sentinel-secret'
