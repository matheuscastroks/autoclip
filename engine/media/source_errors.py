"""Actionable source errors; never expose raw downloader output or credentials."""
from engine.contracts import PipelineError

MESSAGES={
 'SOURCE_AUTH_REQUIRED':'O YouTube bloqueou o download e pediu confirmação de acesso. Use um arquivo local deste vídeo ou tente novamente mais tarde.',
 'SOURCE_RATE_LIMIT':'O YouTube limitou os downloads desta conexão (HTTP 429). Aguarde antes de tentar novamente ou use um arquivo local.',
 'SOURCE_NOT_FOUND':'O arquivo não foi encontrado ou está vazio. Selecione um vídeo local disponível.',
 'SOURCE_UNSUPPORTED':'Este endereço não é suportado. Use um link do YouTube ou um arquivo local.',
 'SOURCE_INVALID':'Não foi possível ler vídeo e áudio desta fonte. Selecione um arquivo de vídeo válido.',
 'SOURCE_UNAVAILABLE':'Não foi possível obter o vídeo. Verifique o endereço e a conexão ou selecione um arquivo local.'}

def source_error(text):
    text=str(text).lower()
    code='SOURCE_AUTH_REQUIRED' if ('not a bot' in text or 'sign in to confirm' in text) else 'SOURCE_RATE_LIMIT' if ('429' in text or 'too many requests' in text) else 'SOURCE_UNAVAILABLE'
    return PipelineError(code,'import',MESSAGES[code],code in ('SOURCE_RATE_LIMIT','SOURCE_UNAVAILABLE'))
