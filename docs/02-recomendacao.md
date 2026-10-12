# Recomendação técnica e decisões propostas

Estado: OpenShorts escolhido pelo usuário como base; especificação de adaptação para revisão; nenhuma interface implementada. A prioridade é preservar a fala e permitir auditoria, inclusive quando o modelo erra.

## Três caminhos

| Caminho | Benefício | Custo/risco | Decisão |
|---|---|---|---|
| Fork seletivo do OpenShorts | Reutiliza seleção, legendas, revisão e recut; preserva base preferida | Isolar motor, excluir cloud, auditar dependências e simplificar recursos | Escolhido; recomendado adaptar incrementalmente |
| Motor próprio pequeno com adaptadores e referências MIT | Controle imediato dos contratos e políticas | Recria partes que OpenShorts já oferece | Reserva se os gates falharem |
| Fork seletivo do Autoclip | CLI, API, SQLite e testes próximos da arquitetura alvo | Outra base; prompt e cache ainda precisam de correção | Referência comparativa |

Adaptar OpenShorts mantendo os módulos permissivos existentes atrás de contratos próprios. Usar faster-whisper e FFmpeg; registrar origem/commit de cada módulo reaproveitado. A escolha da base é do usuário, ainda não uma comparação medida da qualidade dos resultados.

## Stack inicial

- Python 3.12 para benchmark e motor; lock separado por plataforma. O runtime integrado encontrado é 3.12.14; Python global 3.14 não atende o limite do candidato Autoclip.
- faster-whisper com modelo multilíngue `small`, `language=pt`, CPU/int8; perfil de precisão com modelo maior após medir RAM/tempo e WER. Não usar `.en`.
- FFmpeg/ffprobe por subprocesso, encoder libx264 e AAC como caminho CPU. Normalizar resolução/orientação/FPS explicitamente e medir sync.
- Gemini por chave de API como provider escolhido para esta máquina, que não comporta LLM local. Enviar somente texto de transcrição/contexto na configuração proposta; mídia e frames permanecem locais. Ollama fica como adapter opcional para outras máquinas. Provider/modelo/versionamento e payload hash registrados; nenhuma troca automática de provedor. Análise Gemini exige internet e está sujeita às condições/quota da conta, sem promessa de custo zero.
- Detector facial por adaptador OpenCV/YuNet ou MediaPipe; escolher pelos testes e licença dos pesos. Inicialmente uma pessoa; cenas independentes e fallback de quadro inteiro quando tracking for incerto.
- PySceneDetect para reset entre cenas. WhisperX/diarização ficam opcionais, fora do mínimo; manter ASR utilizável sem torch adicional, token ou modelo gated.
- SQLite para projetos, revisões e jobs; arquivos JSON versionados para artefatos volumosos. O domínio não depende de FastAPI.
- Vue 3 + TypeScript + Tauri 2 somente depois dos gates do motor; cliente local do mesmo serviço usado pela CLI.

## Política editorial

Selecionar intervalo contínuo que contenha premissa, explicação e conclusão, incluindo ressalvas relevantes. Uma fala boa de 75 segundos pode ser sinalizada para revisão; não truncar um argumento para caber em 60. Na PoC limitar a 60 e rejeitar propostas incompletas, aceitando zero cortes.

O modelo retorna IDs de palavras existentes e evidências, nunca timestamps inventados. Regras estruturais validam o resultado; revisão humana valida o sentido. Não usar score de viralidade como ordenação principal. Ordenar por completude, independência de contexto e densidade informativa, com justificativas verificáveis.

Pausas são removidas apenas quando silêncio acústico e ausência de fala concordam e nenhum intervalo protegido é atingido. A PoC começa sem remoção; o segundo experimento mede proteção e naturalidade. Baixa confiança implica preservar o trecho. Legendas corrigidas não alteram silenciosamente a transcrição original.

## Decisões adiadas com gate definido

| Decisão | Evidência necessária | Gate |
|---|---|---|
| Aprovar a adaptação OpenShorts | Três cortes no vídeo comum, ausência de cloud, teste de retomada/invalidação e ASR/render offline com seleção Gemini | Antes de congelar o motor MVP |
| Detector padrão | Rosto visível, estabilidade e custo CPU no corpus | Antes de habilitar tracking automático por padrão |
| Modelo Gemini de análise | Disponibilidade na conta, resposta estruturada, rubrica editorial e limites/custo configurados | Antes de aceitar sugestões no pipeline |
| ASR de maior precisão | WER, termos críticos, tempos e RSS | Antes de definir presets definitivos |
| Licença do produto e binários | SBOM com textos de licenças, pesos, fontes e FFmpeg | Antes de qualquer pacote público |

As fontes e commits estão no [comparativo](01-investigacao.md). Esta proposta não autoriza atribuir qualidade, velocidade ou autonomia completa a um candidato ainda não executado de ponta a ponta.
