# Abrir e administrar o AutoClip

## No notebook atual

Abra **AutoClip.lnk** ou **Abrir AutoClip.vbs**, na pasta do repositório, com duplo clique. O launcher inicia o serviço local em segundo plano e abre o navegador. Não é necessário usar terminal para administrar projetos. Um segundo clique reutiliza a instância do mesmo aplicativo.

O atalho pode ser copiado para um local conveniente. Ele aponta para este checkout; mover/apagar a pasta exige gerar novamente o atalho. Esta entrega usa o ambiente provisionado no notebook e não é um instalador autossuficiente. Tauri/instalação em máquina limpa continuam no roadmap.

## Biblioteca e projetos

Os projetos em `poc-projects` são registrados automaticamente. A biblioteca mostra os três projetos existentes, inclusive a transcrição completa, o teste Gemini com falha e a prévia manual. **Importar projeto** abre um seletor de pasta. **Novo projeto** aceita arquivo local ou URL YouTube suportada. Abrir uma pasta de projeto existente preserva o estado e não dispara processamento. Novos vídeos seguem importação → transcrição → análise automaticamente sem checkbox de autorização nem configuração manual de tentativas.

Abra um projeto para ver o original, etapas e atividade. A aba **Transcrição** permite consultar e navegar pelos timestamps existentes. O vídeo indicado mantém as 5.414 palavras já processadas; abrir/consultar não repete ASR. **Abrir pasta** mostra os artefatos no Explorer.

**Transcrever vídeo** usa Whisper local. **Iniciar análise** abre o formulário Gemini com modelo e janela de análise. Iniciar a tarefa envia somente a transcrição em texto; a API pode gerar custos. O motor usa a quantidade real de janelas, incluindo subdivisões por caracteres, para dimensionar automaticamente até quatro tentativas por janela (duas de transporte e uma reparação de JSON com até duas tentativas). Esse teto é uma proteção técnica, não uma quantidade obrigatória de chamadas. Cada tentativa é registrada antes do envio. Falhas persistentes encerram a tarefa; não há retries infinitos.

**Gerar prévias** usa somente análise completa existente; não chama Gemini implicitamente. Transcrição/análise/render são ações separadas. Um trabalho pesado por vez, com cancelamento. O painel ao lado do vídeo mostra o estado e uma barra em cada etapa iniciada; animação indica atividade, sem percentual inventado. **Retomar** disponível para tarefas locais interrompidas. Análise e sequência automática interrompidas podem ser reiniciadas com planejamento automático e um novo registro de chamadas. Não são reiniciadas em segundo plano. Fechar a aba não cancela uma tarefa: use **Cancelar**. **Encerrar serviço** fica disponível quando não há tarefa ativa; o próximo duplo clique inicia nova sessão.

## Capas e lixeira

A biblioteca mostra capas extraídas localmente por FFmpeg e armazenadas por hash do original. O ícone de lixeira permite excluir um projeto, com confirmação; **Lixeira de projetos** permite restaurar. Na aba **Cortes**, **Excluir corte** remove o corte das revisões e das novas exportações; **Lixeira de cortes** permite restaurar. A exclusão é reversível: mídia, artefatos e pacotes já exportados continuam no disco. Um projeto com tarefa ativa não pode ser excluído; os demais continuam administráveis. Não há exclusão definitiva nesta versão.

## Configurações e revisão

Em **Configurações**, selecione modelo Whisper local, ferramentas de vídeo e parâmetros de análise. Digite a chave Gemini no campo oculto e clique em **Salvar e validar**: o aplicativo consulta o catálogo antes de substituir a credencial no Gerenciador de Credenciais do Windows. Falhas de validação preservam a chave anterior. **Testar conexão / Atualizar modelos** consulta a chave salva e preenche o seletor com os IDs e nomes retornados pela API. A interface mostra o estado da conexão e a data do teste, sem exibir a chave. Se o modelo selecionado não estiver no catálogo, escolha outro explicitamente antes de salvar. Abrir configurações não faz consulta remota automática.

O teste usa somente `models.list`, sem geração nem envio de transcrição, vídeo, áudio ou frames. Acesso ao catálogo não garante cota de geração nem suporte do modelo ao contrato de análise. Uma chave definida em `GEMINI_API_KEY` tem precedência; remova essa variável e reabra o aplicativo para substituir uma chave diferente pela interface.

Os cortes elegíveis aparecem na aba **Cortes**, com preview, fonte/contexto e motivo. Ouça e marque os cinco critérios editoriais antes de aprovar. A aprovação pertence à revisão atual; alteração dos artefatos exige nova revisão. **Exportar aprovados** gera pacotes locais com MP4, legendas e metadados. Um projeto sem análise válida permanece sem cortes; a prévia manual é identificada e não recebe aprovação semântica nesta fase.

## Duração, pausas e feedback Gemini

Em **Configurações → Coerência, duração e pausas**, escolha a duração preferida e a máxima (até 180 segundos). O padrão para novos trabalhos é preferência de 60 segundos e máximo de 180. A preferência orienta a análise; não obriga encerrar o argumento naquele ponto. O motor rejeita uma proposta que ultrapasse o máximo, sem aparar palavras para fazê-la caber. O intervalo original selecionado tem mínimo técnico de 20 segundos; a redução de pausas pode deixar a exportação mais curta. Alterar a duração não alonga automaticamente propostas de uma análise antiga: inicie uma nova análise com planejamento automático.

**Encurtar silêncios longos** combina Silero VAD local, baixo volume e timestamps de palavras. Só remove o interior de um intervalo sem voz e quieto confirmado, entre palavras inteiras, mantendo margens. Respirações curtas não são alvo. Sem confirmação no áudio, preserva a pausa e informa o motivo. **Preservar todas as pausas** desativa a redução. O EDL registra intervalos originais removidos e a nova linha do tempo; as legendas são remapeadas. Na revisão, **Revisar silêncios removidos** mostra as junções e permite ouvir o original próximo delas. A aprovação audiovisual permanece obrigatória.

Durante a análise, o painel **Análise do Gemini** mostra os resumos que a API envia, por janela e tentativa, e os eventos do aplicativo. Temas e propostas da análise atual aparecem no painel; os cortes finais ficam na área de revisão. O texto do modelo é apresentado como texto, sem executar HTML. Registros técnicos ficam em `.autoclip/jobs/<id>/analysis-events.jsonl` para diagnóstico interno; não há botão, seletor ou modal de histórico na interface. Desativar a exibição nas configurações vale para novas análises. Análise reaproveitada do cache é identificada e não inventa novos resumos ou solicitações.

A integração usa `generate_content_stream`, `include_thoughts` quando `models.get().thinking` confirma suporte, e separa partes marcadas `thought` do JSON final. Para a série 2.5, a opção solicita orçamento dinâmico de pensamento. Pensamento pode consumir mais tokens; as chamadas são dimensionadas automaticamente para novas tarefas da interface; tentativas por falha continuam limitadas. A API disponibiliza resumos, não pensamento interno completo; disponibilidade e conteúdo dependem do modelo. Consulta de capacidade tem timeout próprio e não gera conteúdo. Referências: [thinking e resumos](https://ai.google.dev/gemini-api/docs/generate-content/thinking#thought-summaries), [saídas estruturadas](https://ai.google.dev/gemini-api/docs/structured-output).

## Preparação em outra instalação — para desenvolvimento

Python3.12 e FFmpeg/libass/libx264 são necessários. Instale o lock Python no venv e o projeto editable com extras desktop; em `desktop`, `npm ci` e `npm run build`. Execute `scripts/create_shortcut.ps1` para gerar o atalho. O modelo ASR e as licenças de distribuição são provisionados separadamente. Logs ficam em `.autoclip`, ignorados no Git; não envie credenciais ou mídia junto com logs.

## Validação

Testes automatizados do provedor usam fixtures. A conexão real ao catálogo foi validada separadamente, sem gerar conteúdo. Resultado real da seleção permanece pendente. Consulte `docs/frontend-progress.md` e `poc-results/frontend/` para evidência de testes/startup e os limites da inspeção visual.


### Chamadas automáticas e compatibilidade

A interface não expõe limite de tentativas nem checkbox de envio de texto. O limite antigo salvo nas configurações não restringe novas análises da interface. Trabalhos antigos e seus logs são preservados. Clientes CLI/API que enviam explicitamente `max_calls` ainda usam limite manual; a CLI conserva suas opções. A contagem real continua na sidebar e nos registros técnicos internos. O cancelamento interrompe a sequência. Nenhuma falha autoriza uma repetição infinita.


### Painel equilibrado e leitura da análise

A visão geral divide vídeo e painel em duas colunas iguais; abaixo de 1000 px, usa uma coluna. As quatro etapas ficam em uma grade compacta e o resumo tem sua própria área. O painel mantém o trabalho ativo ou mais recente por data, independentemente da ordem de atualização. Resumos já recebidos não desaparecem quando o lote de eventos consultado avança.

O resumo acompanha novas mensagens automaticamente. Rolar para cima ou usar **Pausar acompanhamento** suspende o movimento; **Acompanhar atualizações** volta ao fim. A barra fica oculta, mas mouse, toque e teclado continuam disponíveis. Os registros técnicos permanecem internos, sem navegação por análises antigas na interface.

**Janela de análise:** intervalo de tempo da transcrição enviado por solicitação; 600 segundos correspondem a 10 minutos de conteúdo original. O motor usa sobreposição de 30 segundos nas divisões para preservar contexto. **Máximo de caracteres:** teto aproximado do texto com IDs de palavras em cada janela; textos densos são subdivididos mesmo dentro do intervalo de tempo. Não inclui todo o prompt e não equivale a tokens ou à capacidade exata do modelo. Valores maiores dão mais contexto por chamada; menores reduzem o tamanho de cada solicitação e podem aumentar o número de chamadas. Nenhum define a duração dos cortes. Os padrões 600 s / 60.000 caracteres podem ser mantidos; controles ficam em ajustes avançados.

Referências de UX consultadas antes da alteração: [NN/g — visibilidade do estado](https://www.nngroup.com/articles/visibility-system-status/), [W3C — status acessíveis](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA22.html), [W3C — pausa da rolagem automática](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR33).
