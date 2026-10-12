# Gemini API na adaptação OpenShorts

Escolha do usuário: notebook sem capacidade para LLM local, análise por chave Gemini. Essa alteração mantém a mídia e os projetos locais, com análise de texto remota explicitamente configurada.

## Suporte existente confirmado

No OpenShorts self-hosted, `app.py::resolve_gemini` resolve `X-Gemini-Key`/Settings ou `GEMINI_API_KEY`; o modelo vem de Settings/`X-Gemini-Model` ou ambiente. `gemini_worker.py` utiliza `google-genai` e `client.models.generate_content`, com schemas de resposta. O dashboard documenta a entrada de chaves em Settings. Isso comprova suporte do candidato, não uma integração já configurada nesta workspace. Fontes: [app.py](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/app.py), [worker](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/gemini_worker.py), [README](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/README.md).

## Fluxo proposto

1. Notebook importa vídeo e transcreve com Whisper CPU.
2. Backend local envia texto e IDs de palavras ao Gemini; nenhuma chave no frontend de distribuição ou nos artefatos.
3. Gemini sugere intervalos, temas, títulos e razões em JSON estruturado.
4. Motor valida referências e limites; usuário revê sentido e contexto.
5. Notebook aplica EDL, tracking, legendas e render FFmpeg.

Análise precisa de internet; ASR/render/revisão não precisam após baixar modelos. Provider/modelo são configuráveis. Disponibilidade, quota e eventuais cobranças dependem da conta e do modelo; não prometer API sempre gratuita.

## Configuração da futura PoC

Credencial inserida localmente em fluxo próprio e guardada no Windows Credential Manager via keyring; para benchmark temporário pode ser lida de variável de ambiente somente no processo. Não pedir a chave no chat, escrever em Git, incluir em URL/log ou persistir em JSON de projeto. Chave ausente/inválida gera erro acionável, sem acessar provider alternativo.

Criar/gerir a chave no [Google AI Studio](https://aistudio.google.com/apikey), conforme a [documentação oficial](https://ai.google.dev/gemini-api/docs/api-key). Não foi criada ou conectada uma chave nesta entrega.

## Dados enviados e controles

Selecionar caminho de análise por transcrição. Desativar `ENABLE_VISION_ANALYSIS` e `ENABLE_DEEP_ANALYSIS`; não chamar seleção visual de vídeo silencioso, autodeterminação remota de layout ou upload de frames. Escolher layout local/manual na PoC. ASR vazio produz NO_SPEECH em vez de enviar vídeo ao Gemini. Essas restrições precisam de teste de payload e de integração: toggles isolados não comprovam que todos os caminhos de mídia foram bloqueados.

Desligar correção automática de transcrição por LLM: texto original é fonte de rastreabilidade; correção de legenda é revisão explícita. Não permitir Gemini retornar comandos FFmpeg livres ou ferramentas: apenas campos estruturados previamente definidos. Schema e evidências protegem fronteiras, mas não provam integridade sem revisão humana.

Salvar usage/token counts se retornados; limitar quantidade de chamadas, tamanho de janelas, concorrência inicial a 1 e tentativas. Implementar cancelamento, retry com backoff para rate limit, falha de autenticação sem retry e aviso de quota. Não estimar custo em moeda sem tabela vigente e modelo da conta.

Gate: uma análise real com chave inserida localmente, payload textual verificado, três sugestões revisadas e render em CPU. Este gate depende da revisão da arquitetura e ainda não foi executado.
