# AutoClip desktop — Tauri 2

> Validação posterior (2026-10-15): o sidecar standalone com Python/frontend e um
> instalador NSIS debug foram gerados e o app iniciou em workspace novo. FFmpeg e
> modelos continuam externos. As evidências e limites atuais estão em
> [native-runtime-validation-2026-10-15.md](native-runtime-validation-2026-10-15.md);
> as evidências da entrega original abaixo são históricas, não QA visual nativa atual.

Esta entrega encapsula a interface Vue existente em uma janela nativa. O motor Python continua por API/CLI e os projetos existentes permanecem no checkout. Não é um instalador autossuficiente para outros computadores.

## Pré-requisitos e build

Na configuração atual, prepare o sidecar antes do build Tauri: execute
`npm --prefix desktop run build`, depois
`.venv/Scripts/python.exe scripts/build_engine_sidecar.py`. PyInstaller está nas
dependências opcionais `desktop`. Regere o sidecar após mudanças no motor ou no
frontend: ele incorpora o `desktop/dist` existente. Sem esse passo, o recurso
`bin/autoclip-engine-x86_64-pc-windows-msvc.exe` pode faltar ou conter uma UI antiga.
Não abra o executável enquanto o bundler ainda estiver regravando-o; para uma
instância ativa, use alvo de build isolado e preserve os jobs em execução.

Windows x64, Rust estável MSVC, Visual Studio Build Tools com workload C++ e Windows SDK, WebView2 e Node/npm. O checkout precisa de `.venv/Scripts/python.exe`, dependências Python e frontend compilado. Execute `scripts/check_tauri_prerequisites.ps1` para inventário. Se o PATH estiver antigo após instalar Rust, abra novo terminal ou adicione `$env:USERPROFILE\.cargo\bin` ao PATH da sessão.

Build local de desenvolvimento: `npm --prefix desktop run desktop:build:local`. Binário em `desktop/src-tauri/target/debug/autoclip-desktop.exe`. Build otimizado: `npm --prefix desktop run desktop:build`, produz `desktop/src-tauri/target/release/autoclip-desktop.exe`; essa variante precisa de compilação e validação próprias. Abra por duplo clique em `Abrir AutoClip Desktop.vbs`. Para abrir por PowerShell/atalho, use `scripts/open_tauri.ps1`; o script resolve caminhos sem shell interpolado e abre sem console persistente. A execução direta do EXE funciona dentro deste checkout; fora dele, defina AUTOCLIP_WORKSPACE para a raiz provisionada.

## Sessão e encerramento

Tauri inicia o supervisor `engine.api.desktop_session` por canal privado stdin/stdout. A sessão contém token e porta loopback; não registre o protocolo ou URL autenticada em logs. O frontend recebe a credencial na inicialização de cada documento, permitindo reload dentro da janela. Não há shell/IPC nativo autorizado para páginas externas.

Abertura reutiliza instância validada pelo PID, horário de criação e comando, sob lock. Leases registram janelas concorrentes. Um motor compartilhado é preservado no fechamento; o compartilhamento é conservador até a próxima instância. Um motor próprio e ocioso é encerrado pelo endpoint autenticado. Resposta 409 significa tarefa ativa: a janela pode fechar, a tarefa continua em background e a próxima abertura reconecta. Não há kill indiscriminado.

Origem externa, novas janelas e downloads externos são bloqueados. A interface existente exporta arquivos pelo motor local e abre pastas pelos endpoints atuais. Falhas de inicialização aparecem na janela; detalhes operacionais do servidor ficam em `.autoclip/server.log`, sem protocolo de credencial.

## Limites desta entrega

Python, Whisper, FFmpeg, fontes e modelos não foram empacotados. Não mover o EXE para outra máquina como se fosse instalador. A distribuição futura precisa de diretório de dados próprio, binários/modelos com licenças e teste de instalação limpa. Não incluir `.autoclip`, transcrições, vídeos ou credenciais no bundle.

A automação nativa de computador não está disponível nesta sessão; a verificação de processo/janela não substitui QA visual do WebView2. Registrar o resultado real da compilação e da abertura abaixo, sem afirmar validação visual que não ocorreu.

## Evidências desta execução

Rust/cargo 1.99.0, MSVC Build Tools2022 e WebView2 155.0.4283.45 confirmados. Build Vue passou. Suíte Python motor/API: 138 testes passaram após correções de concorrência. Revisão independente confirmou draining e stopping/espera de PID. Build Tauri local (--debug --no-bundle) e rebuild final com tauri/custom-protocol passaram. Dois testes Rust passaram. Suíte Vue:64 passaram com1 worker threads (a primeira execução teve timeout de workers sob carga de compilação). Executável local gerado: desktop/src-tauri/target/debug/autoclip-desktop.exe. Processo aberto com título AutoClip, janela válida e Responding=true; motor autenticado saudável e lease desktop registrado. Reprodução, navegação e diálogos no WebView2 permanecem sem inspeção visual nativa nesta sessão. Build otimizado e instalação limpa não foram validados.
