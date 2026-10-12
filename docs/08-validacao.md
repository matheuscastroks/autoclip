# Estado da investigação e validação

Data: 12/10/2026. Base escolhida pelo usuário: OpenShorts. Esta rodada não valida o produto completo, não implementa a interface e não conclui a comparação editorial dos cinco pipelines.

## Concluído

- Cinco snapshots públicos baixados, commit fixado, licenças e dependências inspecionadas. `research/inventory.json` e `research/snapshots/*/evidence.json` preservam metadados e CI consultada.
- Vídeo indicado baixado e decodificado pelo FFmpeg. SHA-256 e ffprobe em `research/results/media-manifest.json`. Fonte MP4 tem 184.894.331 bytes e 1773,194 s; WAV comum 120 s e 3.840.078 bytes.
- FFmpeg 9.0.2 full localizado fora do PATH; filtros ass/subtitles/silencedetect presentes. Build contém `--enable-gpl --enable-version3 --enable-libx264`: não tratar esse binário como LGPL simples.
- Runtime de pesquisa Python 3.12.14, ambiente isolado `research/.venv`; Python global 3.14 preservado. Pacotes congelados em `research/benchmark-requirements.lock.txt`; modelo multilíngue baixado para `research/models/`.
- Peso principal Whisper small: 483.546.902 bytes, SHA-256 `3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671`, em `research/model-manifest.json`. Auditoria de licença para redistribuição não concluída; download foi para benchmark local.
- Steezy: 17 testes próprios passaram; ASR real da amostra comum executado com `small`, CPU/int8 e encoder CPU configurado. Registro em `research/results/steezy-asr.json`.
- Autoclip: 88 testes do subconjunto boundaries/system/db/config passaram; warning de configuração `asyncio_mode` pela ausência de plugin no ambiente parcial. Não executada suíte inteira nem e2e.
- Autoclip: ASR real da amostra comum concluído em CPU/int8, com idioma PT explícito. Registro em `research/results/autoclip-asr.json`.
- OpenShorts: 116 passaram, 2 skipped, 1 falhou no subconjunto selection/ASR/recut/subtitles/local-LLM. JUnit em `research/results/openshorts-tests.xml`. Os testes de LLM usam HTTP simulado: não demonstram seleção real local.
- OpenShorts: ASR real da mesma amostra concluído em CPU/int8 após iniciar com UTF-8. Registro em `research/results/openshorts-asr.json`.
- PRD, arquitetura, modelo de dados/contratos, recomendação, roadmap e plano de testes escritos para revisão.

## Problemas encontrados e tratamento

| Problema observado | Evidência/causa | Tratamento nesta pesquisa |
|---|---|---|
| Download inicial sem formato | yt-dlp sem JS runtime e seletor combinado ausente | Configurar Node existente e vídeo+áudio separados; download concluído |
| faster-whisper 1.2.1 falha com PyAV 19.0.1 | `av.open(..., metadata_errors=...)` não aceita keyword | Fixar PyAV 18.1.0; abertura WAV e ASR Steezy funcionaram |
| Console Windows no ASR OpenShorts | impressão de emoji em cp1252 interrompe transcrição | Reexecutar com `-X utf8`; registrar no bootstrap proposto |
| Tests Windows lendo main.py em cp1252 | `open()` sem encoding causa UnicodeDecodeError | Executar testes com `-X utf8`; erros de encoding não repetiram |
| Fixtures pytest sem temp acessível | sandbox não cria numbered temp no diretório padrão | `--basetemp` explicitamente dentro do workspace |
| Teste de DETAIL_PROMPT_TEMPLATE falha | teste não passa `game_profile_json`, agora requerido pelo template | Falha upstream preservada; adaptar teste/template após revisar comportamento desejado |
| Dois testes de main ignorados | importorskip depende de stack pesada não provisionada | Registrar skips; não contar como aprovação do roteamento completo |
| Ollama indisponível no endpoint padrão | probe fora do sandbox recebeu WinError 10061 em 127.0.0.1:11434 | Seleção semântica local ainda não executada; não migrar automaticamente para API paga |
| Módulos comerciais importados no pipeline | referências a `cloud.*` em main.py | Distribuição permissiva precisa de prova sem cloud; não copiar módulos comerciais |

O venv do runtime integrado precisou de `pip --python research/.venv` a partir do Python global porque ensurepip não terminou; instalações ocorreram dentro do venv, não globalmente. Snapshots upstream não foram modificados para mascarar falhas.

## Smoke comparável na amostra comum

| Candidato | Entrada/modelo/device | Resultado | Tempo observado |
|---|---|---|---|
| Steezy | WAV comum 120 s; small multilíngue; CPU/int8 | Transcrição concluída | 157,112 s |
| OpenShorts | Mesmo WAV/modelo/device; parâmetros próprios de decode | Transcrição concluída | 168,704 s |
| Autoclip | Mesmo WAV/modelo/device; idioma explícito PT | Transcrição concluída | 216,613 s |
| jameselle | Mesmo vídeo reservado no protocolo | Não executado: runtime whisper.cpp/modelo e portabilidade ainda não preparados | Não medido |
| auto-editor | Mesmo vídeo reservado no protocolo | Não executado: binário/build atual ainda não preparado | Não medido |

Esses tempos não incluem download do modelo e não estabelecem superioridade: execução única, settings de decode diferentes e máquina com outras tarefas. Não há WER ou rubrica de sentido preenchidos; os cortes não foram selecionados/renderizados por esses ensaios.

## Ainda pendente

1. ASR da amostra concluído em Autoclip/OpenShorts/Steezy; preparar jameselle/auto-editor se necessário para completar os cinco ensaios aplicáveis. Métricas de execução não equivalem a WER.
2. Seleção real pelo Gemini ainda pendente: chave configurada e listagem de modelos funcionou; tentativas textuais com Gemini 2.5 Flash encontraram HTTP400 (schema corrigido) e HTTP504 (timeout). Limite de 20 tentativas tratado conservadoramente como esgotado; não repetir sem novo orçamento autorizado.
3. Avaliar cortes reais de todos os candidatos aplicáveis com a rubrica editorial; jameselle e auto-editor não receberam benchmark completo Windows nesta rodada.
4. Ground truth humano, WER/timing, cortes de pausas, tracking/reframe, ASS burn, áudio e QA audiovisual do resultado.
5. Conferir a stack mínima MIT sem cloud/Ultralytics/Remotion obrigatórios; pacote público ainda exige SBOM/licença aprovada.
6. PoC CLI/motor implementada após aprovação: contratos, importação, ASR CPU, análise textual configurável, EDL protegida, captions, render 9:16 fit-blur, QA, retomada e exportação com aprovação humana. Interface desktop permanece fora desta fase.

## Validação da PoC implementada

Suite final: **52 passed, 1 skipped**, 71,92 s; JUnit em `poc-results/tests.xml`. O skip é o teste opt-in de seleção Gemini real, pois não existe análise integral bem-sucedida. Regressões exercitam VFR, silêncio digital, cancelamento, cache, referências, payload textual, schema e orçamento. Não medem qualidade editorial automaticamente.

ASR integral do vídeo indicado: **5.414 palavras**, **2.841,406 s** (~47 min), CPU/int8, small multilíngue. Relógio do vídeo: 1773,183 s; duração de container: 1773,194 s. ASR e mídia ficam locais e ignorados no Git. Reuso no ensaio Gemini identifica explicitamente o artefato e a proveniência, sem repetir inferência.

Preview manual de 25,67 s com legendas e fit-blur passou QA técnica e inspeção de frames. Ele não foi escolhido pelo Gemini nem recebeu aprovação editorial. A comparação semântica dos cinco projetos, WER/timing humanos e aceitação de cortes reais continuam pendentes.

Google documenta `response_json_schema` para saída estruturada ([referência oficial](https://ai.google.dev/gemini-api/docs/structured-output)). A tentativa anterior via `response_schema` foi rejeitada por `additional_properties`; regressão de wire observada RED -> GREEN. A análise de toda a fonte em uma única chamada encontrou timeout HTTP504 de 60 s. Nenhum corte semântico real foi aprovado ou exportado.

## Como reproduzir os ensaios

Scripts Python usam caminhos absolutos do FFmpeg desta máquina, documentados nos arquivos; outra máquina precisa ajustar esse path. O vídeo fica fora do Git. Não são instaladores do produto.

```powershell
python research_collect.py
python research/audit_snapshots.py
python research/download_test_video.py
python research/prepare_media.py
research/.venv/Scripts/python.exe -X utf8 research/benchmark_asr.py steezy --download-model
research/.venv/Scripts/python.exe -X utf8 research/benchmark_asr.py openshorts
research/.venv/Scripts/python.exe -X utf8 research/benchmark_asr.py autoclip
```

Antes do último comando, aguardar término do anterior para não disputar CPU. O ensaio Autoclip força `resolve_compute` para CPU/int8 e idioma `pt`; isso é adaptação de benchmark documentada, não modo nativo. Steezy/OpenShorts autodetectam idioma. Nenhum desses ensaios parciais mede escolha semântica.

Snapshots e locks identificam o que foi analisado; execução única, parâmetros diferentes e tarefas concorrentes do computador impedem um ranking de desempenho. Tempos são registros de smoke, sem promessa para o vídeo integral.
