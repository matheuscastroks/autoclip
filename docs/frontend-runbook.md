# Abrir e administrar o AutoClip

## No notebook atual

Abra **AutoClip.lnk** ou **Abrir AutoClip.vbs**, na pasta do repositório, com duplo clique. O launcher inicia o serviço local em segundo plano e abre o navegador. Não é necessário usar terminal para administrar projetos. Um segundo clique reutiliza a instância do mesmo aplicativo.

O atalho pode ser copiado para um local conveniente. Ele aponta para este checkout; mover/apagar a pasta exige gerar novamente o atalho. Esta entrega usa o ambiente provisionado no notebook e não é um instalador autossuficiente. Tauri/instalação em máquina limpa continuam no roadmap.

## Biblioteca e projetos

Os projetos em `poc-projects` são registrados automaticamente. A biblioteca mostra os três projetos existentes, inclusive a transcrição completa, o teste Gemini com falha e a prévia manual. **Importar projeto** abre um seletor de pasta. **Novo projeto** aceita arquivo local ou URL YouTube suportada. Importar não dispara transcrição/análise.

Abra um projeto para ver o original, etapas e atividade. A aba **Transcrição** permite consultar e navegar pelos timestamps existentes. O vídeo indicado mantém as 5.414 palavras já processadas; abrir/consultar não repete ASR. **Abrir pasta** mostra os artefatos no Explorer.

**Transcrever vídeo** usa Whisper local. **Configurar análise** abre o formulário Gemini, com modelo, janelas e limite de tentativas. É necessário confirmar envio somente de texto; a API pode gerar custos. O orçamento de cada trabalho é persistido antes de cada chamada, incluindo retries/repair. O botão não deve ser usado para repetir o ensaio antigo sem novo orçamento consciente.

**Gerar prévias** usa somente análise completa existente; não chama Gemini implicitamente. Transcrição/análise/render são ações separadas. Um trabalho pesado por vez, com cancelamento; **Retomar** disponível para tarefas locais interrompidas. Análise interrompida exige um novo orçamento explícito e não é retomada automaticamente. Fechar a aba não cancela uma tarefa: use **Cancelar**. **Encerrar serviço** fica disponível quando não há tarefa ativa; o próximo duplo clique inicia nova sessão.

## Configurações e revisão

Em **Configurações**, selecione modelo Whisper local, ferramentas de vídeo e parâmetros de análise. A chave Gemini é digitada em campo oculto e salva no Gerenciador de Credenciais do Windows. A interface mostra apenas presença da chave salva. Não há teste remoto automático nem upload de vídeo/áudio/frames.

Os cortes elegíveis aparecem na aba **Cortes**, com preview, fonte/contexto e motivo. Ouça e marque os cinco critérios editoriais antes de aprovar. A aprovação pertence à revisão atual; alteração dos artefatos exige nova revisão. **Exportar aprovados** gera pacotes locais com MP4, legendas e metadados. Um projeto sem análise válida permanece sem cortes; a prévia manual é identificada e não recebe aprovação semântica nesta fase.

## Preparação em outra instalação — para desenvolvimento

Python3.12 e FFmpeg/libass/libx264 são necessários. Instale o lock Python no venv e o projeto editable com extras desktop; em `desktop`, `npm ci` e `npm run build`. Execute `scripts/create_shortcut.ps1` para gerar o atalho. O modelo ASR e as licenças de distribuição são provisionados separadamente. Logs ficam em `.autoclip`, ignorados no Git; não envie credenciais ou mídia junto com logs.

## Validação

Testes do provedor usam fixtures. Nenhuma chamada real Gemini é feita na validação da interface. Resultado real da seleção permanece pendente. Consulte `docs/frontend-progress.md` e `poc-results/frontend/` para evidência de testes/startup e os limites da inspeção visual.
