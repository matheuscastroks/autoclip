# Investigação dos candidatos

Data de consulta: 12/10/2026. Escopo: os cinco repositórios indicados, no commit efetivamente obtido pela API GitHub. Documentação, código observado e execução são evidências diferentes. Compatibilidade inferida não significa execução aprovada. Não foi medido percentual de cobertura de testes.

## Identidade, manutenção e licença

| Projeto | Commit consultado | Último commit UTC | Situação observada |
|---|---|---|---|
| Gutsken/Autoclip | `5d0eac36fa615b79dd2104083bf273a96f8d68bb` | 01/08/2026 | Fork de artbyjazi/autoclip; alpha; sem releases retornadas |
| Marsic1/openshorts | `b1f5350fcf24b17cb48b581400c35ad9f3974ba5` | 02/09/2026 | Fork de mutonby/openshorts; sem releases retornadas |
| Steezy-code/clipper | `eda13985b1d93333baf8dc44327c65e552a782be` | 11/07/2026 | Repositório independente; sem releases retornadas |
| jameselle/clipper | `ee284c8e9e6aa598e26dd9e2254da6195e308f01` | 08/10/2026 | Repositório independente; sem releases retornadas |
| WyattBlue/auto-editor | `ca3626bd21d944af43079f43e5e90c69c57d018c` | 11/10/2026 | Repositório independente; release mais recente retornada: 31.7.2, de 03/10 |

Nenhum estava arquivado. A ausência de runs nas respostas dos forks não comprova ausência de CI no upstream. O badge do Autoclip aponta para outro repositório: não usar esse badge como validação do fork.

| Projeto | Licença do código | Consequência para integração/redistribuição |
|---|---|---|
| Autoclip | MIT | Conservar licença e copyright nas partes reaproveitadas; auditar fontes/modelos/binários separadamente |
| OpenShorts | MIT, exceto `cloud/` | `cloud/LICENSE` é comercial, com restrições de prestação a terceiros e redistribuição remunerada; excluir esse diretório de qualquer base open source permissiva |
| Steezy | MIT | Reaproveitamento possível com avisos; confirmar licença dos pesos YuNet e de qualquer mídia opcional |
| jameselle | MIT | Código reaproveitável; Claude Code e pesos whisper.cpp não são cobertos pela licença do projeto |
| auto-editor | Unlicense no repositório | Binários de releases incluem dependências com outras licenças; não presumir binário inteiramente em domínio público |

Fontes primárias: [Autoclip LICENSE](https://github.com/Gutsken/Autoclip/blob/5d0eac36fa615b79dd2104083bf273a96f8d68bb/LICENSE), [OpenShorts LICENSE](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/LICENSE), [cloud/LICENSE](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/cloud/LICENSE), [Steezy LICENSE](https://github.com/Steezy-code/clipper/blob/eda13985b1d93333baf8dc44327c65e552a782be/LICENSE), [jameselle LICENSE](https://github.com/jameselle/clipper/blob/ee284c8e9e6aa598e26dd9e2254da6195e308f01/LICENSE), [auto-editor LICENSE](https://github.com/WyattBlue/auto-editor/blob/ca3626bd21d944af43079f43e5e90c69c57d018c/LICENSE).

## Arquitetura e dependências observadas

**Autoclip.** Python 3.11–3.12, FastAPI, CLI Typer, SQLite e frontend React/Vite. Estágios distintos e diretórios de artefatos por job; faster-whisper, MediaPipe, PySceneDetect, pysubs2 e FFmpeg. Provedores Anthropic, OpenAI compatível, Gemini e Ollama. Diarização WhisperX é extra. É a referência mais próxima da separação solicitada, mas retomada baseada na existência de arquivos precisa ganhar hashes, versões e invalidação de dependências. O provider padrão é Anthropic, e o limite padrão chega a 90 segundos: configurar local e 60 segundos explicitamente. Fontes: [pyproject](https://github.com/Gutsken/Autoclip/blob/5d0eac36fa615b79dd2104083bf273a96f8d68bb/pyproject.toml), [runner](https://github.com/Gutsken/Autoclip/blob/5d0eac36fa615b79dd2104083bf273a96f8d68bb/backend/autoclip/pipeline/runner.py), [config](https://github.com/Gutsken/Autoclip/blob/5d0eac36fa615b79dd2104083bf273a96f8d68bb/backend/autoclip/config.py).

**OpenShorts.** Plataforma Python/FastAPI com dashboard React, módulos de seleção, transcrição, layouts e recut; inclui billing, publicação, TTS e serviços de renderização fora do briefing. Dependências pesadas: torch, torchvision, Ultralytics, TransNetV2, MediaPipe; também faster-whisper, Gemini, OpenAI e boto3. O backend LLM configurável permite endpoints locais. Isolar o motor exige mais trabalho que a extensão de um pipeline compacto. Fontes: [requirements](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/requirements.txt), [main](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/main.py), [LLM backend](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/llm_backend.py).

**Steezy.** Pacote Python dividido em transcribe, score, trim, crop, captions e pipeline, servido por FastAPI com frontend JS simples. faster-whisper, OpenCV, NumPy, requests, FFmpeg e Ollama. O render de um corte pode reutilizar transcrição, mas o README avisa que os arquivos de saída não estão separados por job. É simples para experimentar; gerência persistente de projetos precisa ser construída. Fontes: [arquitetura](https://github.com/Steezy-code/clipper/blob/eda13985b1d93333baf8dc44327c65e552a782be/ARCHITECTURE.md), [pipeline](https://github.com/Steezy-code/clipper/blob/eda13985b1d93333baf8dc44327c65e552a782be/clipper/pipeline.py).

**jameselle.** Node/TypeScript, CLI, funções de timeline e revisão web. FFmpeg e whisper.cpp executados como processos externos. A seleção automática é uma skill de Claude Code; uma especificação manual permite render sem esse agente. Tem mapeamento saída→origem e revisão por notas, úteis como referências de edição não destrutiva. Fonte: [README](https://github.com/jameselle/clipper/blob/ee284c8e9e6aa598e26dd9e2254da6195e308f01/README.md), [timeline](https://github.com/jameselle/clipper/blob/ee284c8e9e6aa598e26dd9e2254da6195e308f01/lib/timeline.ts).

**auto-editor.** O commit atual usa Nim 2.2.2+, nimcrypto e integração nativa com FFmpeg; não assumir arquitetura Python com base em versões antigas. Produz timelines e formatos de editores. Possui transcrição opcional integrada via whisper.cpp/Parakeet; seu objetivo principal continua sendo classificação temporal por áudio/movimento e aplicação de ações. Serve melhor como ferramenta auxiliar por CLI que como base de seleção editorial. Fontes: [ae.nimble](https://github.com/WyattBlue/auto-editor/blob/ca3626bd21d944af43079f43e5e90c69c57d018c/ae.nimble), [transcribe](https://github.com/WyattBlue/auto-editor/blob/ca3626bd21d944af43079f43e5e90c69c57d018c/src/transcribe.nim), [README](https://github.com/WyattBlue/auto-editor/blob/ca3626bd21d944af43079f43e5e90c69c57d018c/README.md).

## Windows, CPU e português

| Projeto | Windows observado no código/docs | CPU | Português brasileiro |
|---|---|---|---|
| Autoclip | CI declarada em Windows 3.12, doctor, tratamento de paths/DLLs | ASR e encoder têm caminhos CPU | Whisper `small` multilíngue e language configurável; qualidade ainda não medida |
| OpenShorts | Caminho Docker documentado; CI inspecionada em Ubuntu | Whisper padrão `cpu/int8`; fallback CUDA→CPU | `small` multilíngue; backend Parakeet opcional inclui `pt`; sem prova de precisão PT-BR |
| Steezy | setup.ps1 e tratamento de DLLs | ASR `cpu/int8`; render exige `USE_NVENC=0` | `base.en` padrão inadequado; trocar `WHISPER_MODEL=small` ou outro multilíngue |
| jameselle | README exige Mac/Linux; busca whisper-cli usa `sh`; fontes padrão macOS | whisper.cpp e FFmpeg podem usar CPU | `small.en` padrão inadequado; multilíngue e language precisam de avaliação/adaptação |
| auto-editor | Builds para Windows no sistema de build; binários publicados | Áudio/movimento e render local | Transcrição opcional com linguagem; confirmar recursos do binário escolhido e modelo multilíngue |

Em Steezy, a detecção automática de CUDA para ASR não desliga o encoder NVENC. Não tratar “GPU opcional” do README como prova de execução em máquina CPU. Em jameselle, mudar apenas o modelo não comprova funcionamento em português: conferir language, alinhamento e render. Fontes: [Steezy config](https://github.com/Steezy-code/clipper/blob/eda13985b1d93333baf8dc44327c65e552a782be/clipper/config.py), [jameselle CLI](https://github.com/jameselle/clipper/blob/ee284c8e9e6aa598e26dd9e2254da6195e308f01/clip.ts), [OpenShorts ASR](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/transcribe_backends.py).

## Matriz de capacidades

Legenda: **observado** = código/docs identificados; **parcial** = insuficiente para o requisito; **pendente** = qualidade não avaliada no vídeo comum.

| Critério | Autoclip | OpenShorts | Steezy | jameselle | auto-editor |
|---|---|---|---|---|---|
| Seleção semântica | LLM por janelas com índices de palavras | LLM, deduplicação e snap | Ollama/Qwen, scores de viralidade | Agente Claude Code externo ao motor | Sem seletor editorial equivalente observado |
| Preservação do argumento | Pendente; prompt contém risco explícito | Pendente; polimento de transcrição deve ser desligado | Pendente; score de viralidade não prova sentido | Pendente; QA lexical não prova sentido | Áudio/movimento não prova sentido |
| Pausas internas | Mapa de silêncio ajusta bordas; remoção interna não observada no runner | Recuts/EDL observados; remoção automática segura não demonstrada | Gaps ASR + padding, sem análise acústica | silencedetect ou gaps; padding; QA posterior | Métodos áudio/movimento + margens; sem proteção lexical suficiente |
| Rosto/reframe | MediaPipe, cenas e crop paths | MediaPipe/YOLO, layouts e tracking | YuNet/Haar, maior rosto, suavização | crop/focusX ou fit-blur; tracking automático não observado | Sem tracking facial equivalente observado |
| Legendas | ASS animado; SRT configurável | ASS/Remotion, edição por palavra | ASS karaoke/boxed/bold | ASS pop, transcrição do áudio final | Transcrição/subtítulos dependem de build; não equivale a editor karaoke |
| Retomada/projeto | Jobs SQLite + artefatos; invalidação parcial | History/checkpoints e recut; complexo | Re-render e cache; namespace parcial | Spec, cache, map e revisão | CLI/timeline; projeto de aplicação externo |
| Integração recomendada | Referência principal de motor e interfaces | Estudar módulos permissivos isolados | Protótipos de trim/reframe como referência | Referência de EDL/revisão/QA | Adaptador CLI opcional para comparação acústica |

O prompt do Autoclip sugere acabar no trecho forte antes de qualificações posteriores. Isso entra em conflito direto com a integridade desejada; um fork deve remover essa preferência e preservar ressalvas/negações. Fonte: [highlight_v1](https://github.com/Gutsken/Autoclip/blob/5d0eac36fa615b79dd2104083bf273a96f8d68bb/backend/autoclip/prompts/highlight_v1.txt).

Steezy corta gaps dos timestamps e pode perder fala que o ASR não reconheceu. jameselle usa silêncio acústico e QA de retenção, mas o limiar documentado de 90% não protege uma negação ou número perdido. Auto-editor permite margens; ainda requer proteção por VAD/palavras antes de aceitar cortes. Fontes: [Steezy trim](https://github.com/Steezy-code/clipper/blob/eda13985b1d93333baf8dc44327c65e552a782be/clipper/trim.py), [jameselle timeline](https://github.com/jameselle/clipper/blob/ee284c8e9e6aa598e26dd9e2254da6195e308f01/lib/timeline.ts).

## Maturidade e testes

Inventário estático: Autoclip 12 arquivos `test_*.py` mais conftest, ~287 definições; OpenShorts 64 mais conftest, ~801; Steezy 1 arquivo com 17 testes mais `__init__`; jameselle 4 arquivos e ~75 chamadas `test()`. Contagens são aproximações por padrão textual, sem coleta de parametrizações, sem cobertura. Para auto-editor, o contador Python/TS não se aplica: há testes Nim e workflows build/smoke.

Autoclip declara CI multissistema e render real; e2e depende de mídia fornecida, golden set permanece um gate declarado. OpenShorts CI inspecionada instala dependências leves e deixa ML atrás de gates: passar nessa suíte não valida pesos reais. Steezy tem testes assert-based e nenhum workflow de testes no snapshot; runs de dependency graph não são testes. jameselle tem suíte maior que os 27 citados no README; nenhuma CI no snapshot. Auto-editor tem smoke bem-sucedido no SHA consultado; isso é evidência de manutenção, não benchmark editorial. Fontes: [Autoclip CI](https://github.com/Gutsken/Autoclip/blob/5d0eac36fa615b79dd2104083bf273a96f8d68bb/.github/workflows/ci.yml), [OpenShorts CI](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/.github/workflows/ci.yml), [auto-editor smoke](https://github.com/WyattBlue/auto-editor/actions/runs/38185490603).

## Dependências e licença de distribuição

Ultralytics exige analisar AGPL-3.0 ou licença comercial; um projeto open source pode optar por cumprir AGPL, mas não herda automaticamente MIT do OpenShorts. Remotion possui termos próprios de uso/licenciamento e precisa de auditoria por versão antes de redistribuir. FFmpeg muda de LGPL para GPL conforme os componentes, incluindo libx264; registrar a configuração e atender as obrigações do binário distribuído. Invocar por subprocesso não apaga essas obrigações. Pesos ASR/LLM/detector, fontes e SDKs entram no inventário separado. Fontes: [Ultralytics](https://www.ultralytics.com/license), [Remotion](https://www.remotion.dev/docs/license), [FFmpeg](https://ffmpeg.org/legal.html).

## Matriz de decisão para este briefing

Aplicar gates antes de somar preferências. Não criar nota numérica de qualidade a partir do README.

| Gate | Autoclip | OpenShorts | Steezy | jameselle | auto-editor |
|---|---|---|---|---|---|
| Autonomia sem API paga | Configurável com Ollama | Configurável via endpoint local | Caminho principal local | Seleção automática acoplada a Claude Code | Local, sem seleção equivalente |
| Base permissiva simples | MIT; auditar dependências | Exige excluir cloud e rever Ultralytics/Remotion | MIT; auditar modelos | MIT; retirar acoplamento do seletor | Unlicense fonte; auditar binário |
| Windows CPU sem alteração relevante | Candidato mais favorável; execução pendente | Maior custo de dependências | Requer configurar modelo e encoder | Requer portabilidade e modelo/language | Binário possível; recursos limitados ao escopo auxiliar |
| Fala/semântica no vídeo comum | Pendente | Pendente | Pendente | Pendente | Não compete como seletor |
| Adequação da arquitetura | Mais próxima | Ampla e acoplada a plataforma | Compacta, gestão incompleta | Boa EDL; motor em outra stack | Ferramenta auxiliar |

**Decisão do usuário:** OpenShorts será a base. A adequação documental do Autoclip continua útil como referência de contratos e retomada. Não há vencedor de qualidade semântica comprovado. O fork OpenShorts precisa passar pelos gates de licença, CPU, autonomia e integridade antes de ser considerado base validada. O estado executado está em [validação](08-validacao.md).

**Inspeção adicional após a escolha:** `main.py` importa `cloud.semantic_analyzer`, `cloud.semantic_scoring` e módulos de perfis locais, alguns em blocos de fallback. Portanto, desligar billing não basta para comprovar que o produto distribuído está livre de código comercial. Remover esses módulos da distribuição e testar a seleção permissiva sem eles. Recursos chamados “semantic analyzer” dentro de `cloud/` não serão reaproveitados; a seleção por transcrição fora de `cloud/` é a base a avaliar. Fonte: [main.py](https://github.com/Marsic1/openshorts/blob/b1f5350fcf24b17cb48b581400c35ad9f3974ba5/main.py).
