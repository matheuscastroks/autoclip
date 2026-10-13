# Aplicação desktop Tauri 2 — desenho de integração

Data: 12/10/2026. Escopo para aprovação antes de implementação.

## Resultado

Abrir AutoClip em janela nativa Windows com Tauri 2, reutilizando Vue, FastAPI, SQLite e todos os projetos e configurações existentes. O motor continua independente da janela, por CLI/API. Nenhuma chamada Gemini nem renderização é iniciada pela migração.

## Primeira entrega

Adicionar desktop/src-tauri com aplicação Rust, configuração Tauri e comandos de build. A janela inicia um supervisor Python usando o ambiente provisionado deste checkout. O supervisor reutiliza o lock, valida a identidade da instância existente e obtém uma sessão autenticada sem imprimir credenciais em logs. Uma resposta estruturada pelo canal privado de subprocesso informa a origem loopback e se a instância pertence à janela.

A janela carrega a interface servida pela API em 127.0.0.1, com porta aleatória e autenticação de sessão. A URL de autenticação não é registrada em logs. Não conceder capacidades Tauri a páginas externas; impedir navegação da janela para origens externas. Não expor comandos shell genéricos ao frontend. Downloads e links externos devem ter tratamento explícito.

A inicialização mostra estado e erros legíveis, sem bloquear a thread de UI. Não manter console Windows aberto. A interface atual no navegador permanece disponível como alternativa.

## Fechamento e propriedade

Fechar a janela não cancela análise nem renderização. Se houver trabalho ativo, explicar que o motor continuará em segundo plano; ele pode ser acessado numa próxima abertura. Se estiver ocioso e tiver sido iniciado exclusivamente pela janela, solicitar encerramento pelo endpoint autenticado e aguardar saída. Não encerrar um motor compartilhado já existente nem usar encerramento indiscriminado de processos. Reabertura reutiliza a sessão validada.

## Distribuição

Este lote entrega a janela nativa para o ambiente local já provisionado. Não anunciar um instalador autossuficiente: Python, FFmpeg e Whisper ainda dependem da instalação existente. Empacotar Python/modelos/bibliotecas, definir diretório de dados fora da instalação e validar máquina limpa constitui a etapa seguinte, conforme M5. Não incluir chaves, projetos, logs nem vídeos em bundles.

Rust/Cargo não foram encontrados no PATH ou no diretório padrão do usuário. Verificar instalações alternativas, MSVC Build Tools e WebView2 antes de instalar o que estiver ausente, usando fontes oficiais. Documentar resultado real do build.

## Validação e aceite

- Testes do supervisor: reutilização, instância estrangeira, falha de startup, posse e encerramento sem cancelar jobs.
- Build TypeScript/Vue, cargo check e build Windows quando pré-requisitos estiverem disponíveis.
- Abrir a janela nativa e conferir biblioteca, configurações, tabela de cortes e reprodução MP4/WebView2.
- Fechar/reabrir preserva projetos, configurações e decisões; confirmar comportamento durante tarefa ativa por teste controlado, sem APIs pagas.
- Logs sem credenciais; URL externa não ganha acesso a comandos nativos.
- Relatar separadamente validação automatizada, visual e distribuição em máquina limpa.

## Referências

https://v2.tauri.app/reference/config/
https://v2.tauri.app/start/prerequisites/
https://v2.tauri.app/distribute/windows-installer/
