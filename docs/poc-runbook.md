# Executar a PoC OpenShorts + Gemini

Esta PoC fornece o motor por CLI. ASR, edição, captions e render rodam em CPU; somente texto é enviado ao Gemini. Desktop, API, SQLite, face tracking e remoção automática de pausas estão nos marcos seguintes.

## Ambiente testado

Python 3.12.14 em `.venv`, FFmpeg/ffprobe 9.0.2 full, faster-whisper 1.2.1 e PyAV 18.1.0. O detector procura FFmpeg no PATH e em WinGet. O Python global 3.14 não atende a versão desta PoC. Não são necessárias CUDA, Ollama ou Docker.

Para outra máquina: instale Python 3.12 e FFmpeg com libass/libx264; crie `.venv` com esse Python e instale `requirements-poc.lock.txt`, seguido de `pip install --no-deps -e .`. O código novo é MIT; os notices upstream ficam em `THIRD_PARTY_NOTICES.md`. Não há FFmpeg/modelo/fonte proprietária incluídos no Git.

No notebook atual o pacote está instalado. Execute no diretório `C:\Users\Matheus\Projects\autoclip-editor`:

```powershell
.\.venv\Scripts\autoclip-engine.exe doctor
.\.venv\Scripts\autoclip-engine.exe --help
```

## Configurar Gemini sem expor a chave

```powershell
.\.venv\Scripts\autoclip-engine.exe auth set-gemini-key
```

A entrada é oculta e persistida no Windows Credential Manager. Copie a chave do Google AI Studio, não senha de conta. Caracteres inválidos são rejeitados sem ecoar o segredo. Se o keyring não estiver acessível, a CLI aceita `GEMINI_API_KEY` no ambiente do processo e não grava fallback plaintext. Nunca envie a chave ao chat nem ao Git. O sandbox pode não enxergar o Credential Manager; o diagnóstico fora dele retorna só presença/validade.

O modelo é um parâmetro obrigatório, selecionado entre os modelos disponíveis à conta. O teto de chamadas também é obrigatório; inclui retries e uma eventual reparação de JSON. A execução não escolhe outro provider automaticamente.

## Rodar o vídeo escolhido

```powershell
.\.venv\Scripts\autoclip-engine.exe run .\research\media\z0cf-eWBVCo.mp4 --project .\poc-projects\gemini-test --model NOME_DO_MODELO --max-calls 20
```

Substitua `NOME_DO_MODELO` por um ID disponível na conta e ajuste o teto de chamadas antes de executar. Neste ensaio o usuário autorizou Gemini 2.5 Flash e até 20 tentativas; esse orçamento está conservadoramente esgotado após erros de schema e timeout. Não repetir `run`/`resume` remoto sem novo orçamento. A análise usa somente texto. Orçamento insuficiente para todas as janelas é rejeitado antes de chamar o provedor.

Whisper small multilíngue está em `research/models/whisper-small` nesta máquina. Para outro local, use `--asr-model CAMINHO`. Importação e ASR do vídeo completo podem levar muitos minutos em CPU; o benchmark de 120 s não é uma previsão de tempo integral.

## Retomar, revisar e exportar

```powershell
.\.venv\Scripts\autoclip-engine.exe resume --project .\poc-projects\gemini-test
.\.venv\Scripts\autoclip-engine.exe review --project .\poc-projects\gemini-test
.\.venv\Scripts\autoclip-engine.exe approve UUID_DA_REVISAO --project .\poc-projects\gemini-test
.\.venv\Scripts\autoclip-engine.exe export --project .\poc-projects\gemini-test
```

`review` gera HTML local com original, preview, timestamps e contexto ±30 s. Ouça cada vídeo inteiro, conferindo negações, números, premissas, conclusões e ressalvas; ampliar contexto quando necessário. `approve` pergunta por cinco critérios humanos. Qualquer critério não confirmado rejeita o corte. Não confunda testes com decisão humana sobre conteúdo real.

`export` só aceita revisão aprovada cujo fingerprint ainda corresponda à EDL, candidato, legenda, render e QA. Modificar esses artefatos exige nova aprovação. O pacote contém MP4, ASS, SRT, word JSON, EDL, metadados, checksums e proveniência; a mídia original é preservada. Os manifests de etapas ficam no projeto e validam reutilização por hashes.

## Testes e evidências

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests -q --basetemp .test-tmp
```

`tests/real_media/test_pipeline_real.py` depende de um projeto Gemini real: configure `AUTOCLIP_REAL_PROJECT` somente depois de executar esse projeto. Um skip com razão não é validação semântica.

A investigação e a PoC são registros distintos. O preview em `poc-projects/manual-render-check/` é um teste manual de render com captions do smoke 60–180 s, com flags editoriais uncertain. Nenhum Gemini foi chamado para selecionar esse trecho; ele não está aprovado. A transcrição completa terminou em `poc-projects/jones-manoel/`: 5.414 palavras em 47 minutos de CPU.

O Git local usa a branch `poc-openshorts-gemini` e commits por etapa. Não foi criado remote nem feito push. Projetos, vídeos, modelos, ambientes e secrets são ignorados.

## Limites que permanecem

Palavras/timestamps ASR são estimativas; ainda não há WER anotado nem garantia automática de integridade. Aprovação editorial real e análise Gemini integral bem-sucedida são gates separados dos 52 testes aprovados (um teste real skipped). HTTP504 bloqueou o ensaio remoto dentro do timeout de 60 s. Um próximo ensaio deve reservar orçamento antes de chamar o provedor e usar janelas intermediárias; a janela integral é uma tentativa documentada, sem validação de qualidade. Distribuição pública requer auditoria de licenças.
