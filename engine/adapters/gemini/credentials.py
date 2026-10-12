import os
import keyring
from engine.contracts import PipelineError

SERVICE='autoclip-editor'

def _validate_key(secret:str) -> str:
    secret=secret.strip()
    if not secret or not secret.isascii() or any(c.isspace() or ord(c)<33 for c in secret):
        raise PipelineError('PROVIDER_AUTH','auth','API key has invalid characters. Re-enter the Google AI Studio key locally; never paste it in chat.')
    return secret

def set_gemini_key(secret: str) -> None:
    secret=_validate_key(secret)
    try: keyring.set_password(SERVICE,'gemini',secret)
    except Exception:
        raise PipelineError('KEYRING_UNAVAILABLE','auth','Credential Manager unavailable; use process environment, never plaintext files.') from None

def get_gemini_key() -> str:
    secret=os.environ.get('GEMINI_API_KEY','').strip()
    if not secret:
        try: secret=keyring.get_password(SERVICE,'gemini') or ''
        except Exception: secret=''
    if not secret: raise PipelineError('PROVIDER_AUTH','analyze','Configure the Gemini key locally using auth set-gemini-key.')
    return _validate_key(secret)
