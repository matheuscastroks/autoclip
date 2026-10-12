"""Credential validation through metadata only; no content generation."""
from datetime import datetime, timezone
import os
from hashlib import sha256
from threading import RLock
from fastapi import HTTPException
from google import genai
from google.genai import types
from engine.contracts import PipelineError
from engine.adapters.gemini.credentials import _validate_key
from . import settings


def list_models(key, client_factory=genai.Client):
    client = client_factory(api_key=key, http_options=types.HttpOptions(
        timeout=15000, retry_options=types.HttpRetryOptions(attempts=1)))
    try:
        rows = {}
        for model in client.models.list(config={'page_size': 1000}):
            if not model.name or not any(a.lower() == 'generatecontent' for a in (model.supported_actions or [])):
                continue
            identifier = model.name.removeprefix('models/')
            rows[identifier] = {'id': identifier, 'name': model.name,
                                'display_name': model.display_name or identifier}
        return list(rows.values())
    finally:
        client.close()


def safe_error(exc):
    code = getattr(exc, 'code', None)
    if code in (400, 401) or isinstance(exc, PipelineError):
        return 400, 'Chave inválida ou não configurada. Confira a chave no Google AI Studio.'
    if code == 403:
        return 403, 'A chave não tem permissão para consultar os modelos Gemini.'
    if code == 429:
        return 429, 'Limite de consultas atingido. Aguarde e teste novamente.'
    return 503, 'Serviço indisponível ou conexão expirada. Confira a internet e tente novamente.'


class GeminiConnection:
    def __init__(self):
        self.catalog = list_models
        self.lock = RLock()
        self.digest = None
        self.result = None

    def status(self):
        with self.lock:
            try:
                key = settings.get_gemini_key()
            except PipelineError:
                return self.empty(False)
            if self.digest == sha256(key.encode()).digest() and self.result:
                return self.result
            return self.empty(True)

    @staticmethod
    def empty(configured):
        return {'status': 'untested' if configured else 'missing', 'configured': configured,
                'checked_at': None, 'message': 'Chave salva; conexão ainda não testada.' if configured else 'Adicione sua chave Gemini.', 'models': []}

    def validate(self, candidate=None):
        with self.lock:
            try:
                key = _validate_key(candidate) if candidate is not None else settings.get_gemini_key()
                if candidate is not None and os.environ.get('GEMINI_API_KEY', '').strip() not in ('', key):
                    raise HTTPException(409, 'Uma chave de ambiente está ativa. Remova GEMINI_API_KEY e reabra o aplicativo para configurar a chave pelo Windows.')
                models = self.catalog(key)
            except HTTPException:
                raise
            except Exception as exc:
                code, message = safe_error(exc)
                if candidate is not None:
                    raise HTTPException(code, message + ' A chave anterior permanece salva.') from None
                result = {**self.empty(self.status()['configured']),
                          'status': 'invalid' if code in (400, 403) else 'unavailable',
                          'checked_at': datetime.now(timezone.utc).isoformat(), 'message': message}
                if 'key' in locals():
                    self.digest = sha256(key.encode()).digest()
                    self.result = result
                return result
            if candidate is not None:
                settings.set_gemini_key(key)
            self.digest = sha256(key.encode()).digest()
            self.result = {'status': 'valid', 'configured': True,
                           'checked_at': datetime.now(timezone.utc).isoformat(),
                           'message': 'Conexão validada.', 'models': models}
            return self.result
