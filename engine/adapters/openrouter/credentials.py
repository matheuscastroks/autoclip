import os
import keyring
from engine.contracts import PipelineError

SERVICE = 'autoclip-editor'
KEY_NAME = 'openrouter'

def _validate_key(secret: str) -> str:
    secret = secret.strip()
    if not secret or not secret.isascii() or any(c.isspace() or ord(c) < 33 for c in secret):
        raise PipelineError('PROVIDER_AUTH', 'auth', 'API key has invalid characters. Re-enter the OpenRouter key locally; never paste it in chat.')
    return secret

def set_openrouter_key(secret: str) -> None:
    secret = _validate_key(secret)
    try:
        keyring.set_password(SERVICE, KEY_NAME, secret)
    except Exception:
        raise PipelineError('KEYRING_UNAVAILABLE', 'auth', 'Credential Manager unavailable; use process environment, never plaintext files.') from None

def get_openrouter_key() -> str:
    secret = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not secret:
        try:
            secret = keyring.get_password(SERVICE, KEY_NAME) or ''
        except Exception:
            secret = ''
    if not secret:
        raise PipelineError('PROVIDER_AUTH', 'analyze', 'Configure the OpenRouter key locally using settings.')
    return _validate_key(secret)
