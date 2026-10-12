# Abrir e administrar o AutoClip

## No notebook atual

Abra **AutoClip.lnk** ou **Abrir AutoClip.vbs**, na pasta do repositório, com duplo clique. O launcher inicia o serviço local em segundo plano e abre o navegador. Não é necessário usar terminal para administrar projetos. Um segundo clique reutiliza a instância do mesmo aplicativo.

O atalho pode ser copiado para um local conveniente. Ele aponta para este checkout; mover/apagar a pasta exige gerar novamente o atalho. Esta entrega usa o ambiente provisionado no notebook e não é um instalador autossuficiente. Tauri/instalação em máquina limpa continuam no roadmap.

## Biblioteca e projetos

Os projetos em `poc-projects` são registrados automaticamente. A biblioteca mostra os três projetos existentes, inclusive a transcrição completa, o teste Gemini com falha e a prévia manual. **Importar projeto** abre um seletor de pasta. **Novo projeto** aceita arquivo local ou URL YouTube suportada. Abrir uma pasta de projeto existente preserva o estado e não dispara processamento. Novos vídeos seguem importação → transcrição → análise automaticamente após a confirmação do envio de texto e do orçamento no formulário de criação.

Abra um projeto para ver o original, etapas e atividade. A aba **Transcrição** permite consultar e navegar pelos timestamps existentes. O vídeo indicado mantém as 5.414 palavras já processadas; abrir/consultar não repete ASR. **Abrir pasta** mostra os artefatos no Explorer.

**Transcrever vídeo** usa Whisper local. **Configurar análise** abre o formulário Gemini, com modelo, janelas e limite de tentativas. É necessário confirmar envio somente de texto; a API pode gerar custos. O orçamento de cada trabalho é persistido antes de cada chamada, incluindo retries/repair. O botão não deve ser usado para repetir o ensaio antigo sem novo orçamento consciente.

**Gerar prévias** usa somente análise completa existente; não chama Gemini implicitamente. Transcrição/análise/render são ações separadas. Um trabalho pesado por vez, com cancelamento. O painel ao lado do vídeo mostra o estado e uma barra em cada etapa iniciada; animação indica atividade, sem percentual inventado. **Retomar** disponível para tarefas locais interrompidas. Análise e sequência automática interrompidas exigem um novo orçamento explícito e não é retomada automaticamente. Fechar a aba não cancela uma tarefa: use **Cancelar**. **Encerrar serviço** fica disponível quando não há tarefa ativa; o próximo duplo clique inicia nova sessão.

## Capas e lixeira

A biblioteca mostra capas extraídas localmente por FFmpeg e armazenadas por hash do original. O ícone de lixeira permite excluir um projeto, com confirmação; **Lixeira de projetos** permite restaurar. Na aba **Cortes**, **Excluir corte** remove o corte das revisões e das novas exportações; **Lixeira de cortes** permite restaurar. A exclusão é reversível: mídia, artefatos e pacotes já exportados continuam no disco. Um projeto com tarefa ativa não pode ser excluído; os demais continuam administráveis. Não há exclusão definitiva nesta versão.

## Configurações e revisão

Em **Configurações**, selecione modelo Whisper local, ferramentas de vídeo e parâmetros de análise. Digite a chave Gemini no campo oculto e clique em **Salvar e validar**: o aplicativo consulta o catálogo antes de substituir a credencial no Gerenciador de Credenciais do Windows. Falhas de validação preservam a chave anterior. **Testar conexão / Atualizar modelos** consulta a chave salva e preenche o seletor com os IDs e nomes retornados pela API. A interface mostra o estado da conexão e a data do teste, sem exibir a chave. Se o modelo selecionado não estiver no catálogo, escolha outro explicitamente antes de salvar. Abrir configurações não faz consulta remota automática.

O teste usa somente `models.list`, sem geração nem envio de transcrição, vídeo, áudio ou frames. Acesso ao catálogo não garante cota de geração nem suporte do modelo ao contrato de análise. Uma chave definida em `GEMINI_API_KEY` tem precedência; remova essa variável e reabra o aplicativo para substituir uma chave diferente pela interface.

Os cortes elegíveis aparecem na aba **Cortes**, com preview, fonte/contexto e motivo. Ouça e marque os cinco critérios editoriais antes de aprovar. A aprovação pertence à revisão atual; alteração dos artefatos exige nova revisão. **Exportar aprovados** gera pacotes locais com MP4, legendas e metadados. Um projeto sem análise válida permanece sem cortes; a prévia manual é identificada e não recebe aprovação semântica nesta fase.

## Duração, pausas e feedback Gemini

Em **Configurações → Coerência, duração e pausas**, escolha a duração preferida e a máxima (até 180 segundos). O padrão para novos trabalhos é preferência de 60 segundos e máximo de 180. A preferência orienta a análise; não obriga encerrar o argumento naquele ponto. O motor rejeita uma proposta que ultrapasse o máximo, sem aparar palavras para fazê-la caber. O intervalo original selecionado tem mínimo técnico de 20 segundos; a redução de pausas pode deixar a exportação mais curta. Alterar a duração não alonga automaticamente propostas de uma análise antiga: uma nova análise exige confirmação do envio de texto e orçamento.

**Encurtar silêncios longos** combina Silero VAD local, baixo volume e timestamps de palavras. Só remove o interior de um intervalo sem voz e quieto confirmado, entre palavras inteiras, mantendo margens. Respirações curtas não são alvo. Sem confirmação no áudio, preserva a pausa e informa o motivo. **Preservar todas as pausas** desativa a redução. O EDL registra intervalos originais removidos e a nova linha do tempo; as legendas são remapeadas. Na revisão, **Revisar silêncios removidos** mostra as junções e permite ouvir o original próximo delas. A aprovação audiovisual permanece obrigatória.

Durante a análise, o painel **Análise do Gemini** mostra os resumos que a API envia, por janela e tentativa, e os eventos do aplicativo. **Ver histórico e propostas** abre os temas, motivos dos cortes e tokens informados, com paginação e atualização durante execução. O texto do modelo é apresentado como texto, sem executar HTML. O histórico fica em `.autoclip/jobs/<id>/analysis-events.jsonl`; trabalhos antigos podem não possuir resumos. Desativar a exibição nas configurações vale para novas análises. Análise reaproveitada do cache é identificada e não inventa novos resumos ou solicitações.

A integração usa `generate_content_stream`, `include_thoughts` quando `models.get().thinking` confirma suporte, e separa partes marcadas `thought` do JSON final. Para a série 2.5, a opção solicita orçamento dinâmico de pensamento. Pensamento pode consumir mais tokens; a quantidade de chamadas continua limitada, incluindo retries/repair. A API disponibiliza resumos, não pensamento interno completo; disponibilidade e conteúdo dependem do modelo. Consulta de capacidade tem timeout próprio e não gera conteúdo. Referências: [thinking e resumos](https://ai.google.dev/gemini-api/docs/generate-content/thinking#thought-summaries), [saídas estruturadas](https://ai.google.dev/gemini-api/docs/structured-output).

## Preparação em outra instalação — para desenvolvimento

Python3.12 e FFmpeg/libass/libx264 são necessários. Instale o lock Python no venv e o projeto editable com extras desktop; em `desktop`, `npm ci` e `npm run build`. Execute `scripts/create_shortcut.ps1` para gerar o atalho. O modelo ASR e as licenças de distribuição são provisionados separadamente. Logs ficam em `.autoclip`, ignorados no Git; não envie credenciais ou mídia junto com logs.

## Validação

Testes automatizados do provedor usam fixtures. A conexão real ao catálogo foi validada separadamente, sem gerar conteúdo. Resultado real da seleção permanece pendente. Consulte `docs/frontend-progress.md` e `poc-results/frontend/` para evidência de testes/startup e os limites da inspeção visual.
