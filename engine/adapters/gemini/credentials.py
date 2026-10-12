import os
import keyring
from engine.contracts import PipelineError

SERVICE='autoclip-editor'

def set_gemini_key(secret: str) -> None:
    if not secret.strip(): raise PipelineError('PROVIDER_AUTH','auth','Empty API key.')
    try: keyring.set_password(SERVICE,'gemini',secret.strip())
    except Exception:
        raise PipelineError('KEYRING_UNAVAILABLE','auth','Credential Manager unavailable; use process environment, never plaintext files.') from None

def get_gemini_key() -> str:
    secret=os.environ.get('GEMINI_API_KEY','').strip()
    if not secret:
        try: secret=keyring.get_password(SERVICE,'gemini') or ''
        except Exception: secret=''
    if not secret: raise PipelineError('PROVIDER_AUTH','analyze','Configure the Gemini key locally using auth set-gemini-key.')
    return secret
