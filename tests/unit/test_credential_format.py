import pytest

def test_non_ascii_key_is_rejected_without_persisting_or_echoing(monkeypatch):
    from engine.adapters.gemini import credentials
    from engine.contracts import PipelineError
    monkeypatch.setattr(credentials.keyring,'set_password',lambda *a:pytest.fail('must not persist invalid key'))
    with pytest.raises(PipelineError) as error:credentials.set_gemini_key('credencial-inválida-de-teste')
    assert 'credencial-inválida' not in str(error.value)
    assert error.value.code=='PROVIDER_AUTH'

def test_invalid_saved_key_is_actionable(monkeypatch):
    from engine.adapters.gemini import credentials
    from engine.contracts import PipelineError
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    monkeypatch.setattr(credentials.keyring,'get_password',lambda *a:'credencial-inválida-de-teste')
    with pytest.raises(PipelineError):credentials.get_gemini_key()
