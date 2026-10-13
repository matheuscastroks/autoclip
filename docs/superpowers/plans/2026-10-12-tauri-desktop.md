# Tauri Desktop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Abrir AutoClip em janela Tauri 2 no Windows com o motor local existente e ciclo de vida seguro.

**Architecture:** Tauri inicia um supervisor Python por subprocesso sem shell. O supervisor reutiliza a instância autenticada existente ou inicia uma própria. A janela recebe a sessão em canal privado e carrega somente a origem loopback da API, preservando o frontend Vue.

**Tech Stack:** Tauri 2, Rust MSVC, WebView2, Vue 3/TypeScript, Python 3.12/FastAPI.

**Spec:** docs/superpowers/specs/2026-10-12-tauri-desktop-design.md

## Global Constraints

- Windows; porta aleatória em 127.0.0.1; nenhuma credencial em logs.
- Motor continua independente da janela por CLI/API.
- Fechar a janela não cancela análise nem renderização.
- Não encerrar motor compartilhado já existente.
- Nenhuma chamada Gemini nem renderização é iniciada pela migração.
- Este lote usa o ambiente provisionado; não representa instalador autossuficiente.
- Não incluir chaves, projetos, logs ou vídeos nos bundles.

## Review Focus

- Caminhos com espaços e acentos devem funcionar sem shell/interpolação.
- Duas aberturas concorrentes não devem disputar o motor ou encerrar a instância compartilhada.
- Falha de startup deve apresentar mensagem utilizável e deixar a janela responsiva.
- Uma tarefa iniciada no instante do fechamento deve impedir shutdown e continuar em background.
- Navegação/download de origem externa não deve executar comandos nativos ou expor a sessão.

## Mapa de arquivos

- engine/api/desktop_session.py: protocolo e posse da sessão para a janela.
- engine/api/launcher.py: aquisição compartilhada de sessão sem abrir navegador.
- tests/api/test_desktop_session.py: testes de lifecycle e protocolo.
- desktop/src-tauri/{Cargo.toml,build.rs,tauri.conf.json,src/main.rs}: shell e build.
- desktop/src-tauri/src/{supervisor.rs,window.rs}: subprocesso/protocolo e janela/navegação.
- desktop/src-tauri/startup.html: estado de inicialização e erros sem API privilegiada remota.
- desktop/package.json/package-lock.json: CLI Tauri e scripts de execução/build.
- scripts/check_tauri_prerequisites.ps1: inventário verificável de Rust/MSVC/WebView2.
- scripts/open_tauri.ps1: abertura local do binário compilado sem console persistente.
- docs/tauri-runbook.md: pré-requisitos, build, limites e funcionamento.

### Tarefa 1 — Sessão e lifecycle do motor

**Interfaces:** acquire_session(workspace: Path) -> tuple[dict, bool], onde bool indica instância iniciada por esta aquisição. Supervisor responde JSON v1 com origin, token e owned; recebe close por stdin e responde stopped, shared, busy ou unavailable. Nunca usar repr/log da sessão.

- [ ] Escrever testes: instância validada retorna owned=false; obsoleta inicia owned=true; protocolo rejeita porta/origem inválida; caminho Unicode preservado; stdout só contém protocolo.
- [ ] Executar pytest tests/api/test_desktop_session.py; confirmar falha antes da implementação.
- [ ] Extrair aquisição do launcher sob seu lock e implementar supervisor sem alterar a abertura no navegador.
- [ ] Testar close: shared não chama shutdown; owned ocioso chama endpoint autenticado; HTTP 409 mantém job/motor; comunicação indisponível não usa kill indiscriminado. Ao EOF, aplicar a mesma política.
- [ ] Implementar posse concorrente conservadora: segunda janela ou reutilização existente impede a primeira de encerrar motor compartilhado, usando registro de leases por processo e validação de identidade.
- [ ] Executar testes de sessão e launcher; commit do lifecycle.

### Tarefa 2 — Janela Tauri e pré-requisitos Windows

**Interfaces:** Rust Supervisor inicia .venv/Scripts/python.exe com argv separado, captura protocolo privado com limite de tamanho, mantém stdin e canal de resposta e fornece session/close. Window usa origin validada e token sem logs; startup assíncrono.

- [ ] Criar inventário de Rust em PATH, .cargo e locais alternativos, MSVC via vswhere/registro e WebView2 via registro. Registrar evidências no runbook.
- [ ] Provisionar somente dependências ausentes via fontes oficiais, com comandos idempotentes e sem janelas visíveis para instaladores não interativos.
- [ ] Adicionar estrutura Tauri 2 e CLI npm com lock, janela 1440x900 e mínimo 1000x680. Manter resize e frontend responsivo.
- [ ] Escrever testes Rust para validação de origin (somente 127.0.0.1 com porta 1024–65535), protocolo incompleto/malformado e resolução de caminhos.
- [ ] Implementar Supervisor e Window; ocultar console Windows; exibir startup/falha na janela sem bloquear UI.
- [ ] Restringir navegação à origem atual, não habilitar IPC nativo em origens externas. Bloquear novas janelas externas por padrão; links externos explícitos usam abertura validada sem token. Downloads continuam pelo fluxo local e não autorizam navegação externa.
- [ ] No fechamento, consultar supervisor assincronamente: busy mostra aviso de processamento em background; shared preserva motor; stopped aguarda saída. Impedir fechar/reabrir handlers recursivamente.
- [ ] Executar cargo test, cargo check, npm run build e build Tauri sem bundle. Commit da janela.

### Tarefa 3 — Abertura e verificação de uso real

**Interfaces:** scripts/open_tauri.ps1 resolve checkout/binário por caminho absoluto e Start-Process -WindowStyle Hidden. Não substitui atalho existente até confirmar a janela funcional.

- [ ] Implementar abertura por duplo clique e documentar build/desenvolvimento e logs sem segredos.
- [ ] Abrir janela nativa: biblioteca, configuração, seleção de uma linha na tabela de cortes, vídeo/legendas e comportamento de resize.
- [ ] Testar fechamento/reabertura sem trabalho e tarefa ativa simulada, preservando arquivos, decisões e sessão compartilhada. Não iniciar chamadas pagas.
- [ ] Validar navegabilidade por teclado, diálogos de arquivo e downloads locais no WebView2; registrar qualquer limite não resolvido.
- [ ] Executar testes Python de API/lifecycle, testes Vue e build final. Atualizar README/runbook com comandos e evidência, distinguindo desenvolvimento de distribuição Windows limpa.
- [ ] Revisar diff completo e riscos de posse/credencial; commit final. Reportar o binário efetivamente produzido e quais verificações nativas foram possíveis.

## Revisão do plano

Cada requisito da especificação está coberto nas tarefas 1–3. Sem empacotamento de modelos/Python neste lote. A política de leases complementa a posse prevista na especificação e evita shutdown indevido entre janelas. A revisão visual nativa dependerá das superfícies de automação disponíveis; não usar evidência do navegador como prova de WebView2.
