# Abrir e administrar o AutoClip

Percentuais medidos, estimativas e avisos de inatividade estão descritos em
[Progresso do processamento](process-progress.md). A nova interface depende de
carregar o motor e os assets atualizados; não reinicie uma tarefa ativa para isso.

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

Os temas e propostas aparecem na aba **Análise**, com justificativa, duração e reprodução do intervalo original. Selecione os trechos e use **Gerar N prévias**. As prévias verificadas aparecem na aba **Cortes**, com fonte/contexto e motivo. Ouça e marque os cinco critérios editoriais antes de aprovar. A aprovação pertence à revisão atual; alteração dos artefatos exige nova revisão. **Exportar aprovados** gera pacotes locais com MP4, legendas e metadados. Um projeto sem análise válida permanece sem cortes; a prévia manual é identificada e não recebe aprovação semântica nesta fase.

## Duração, pausas e feedback Gemini

Em **Configurações → Coerência, duração e pausas**, escolha a duração preferida e a máxima (até 180 segundos). O padrão para novos trabalhos é preferência de 60 segundos e máximo de 180. A preferência orienta a análise; não obriga encerrar o argumento naquele ponto. O motor rejeita uma proposta que ultrapasse o máximo, sem aparar palavras para fazê-la caber. O intervalo original selecionado tem mínimo técnico de 20 segundos; a redução de pausas pode deixar a exportação mais curta. Alterar a duração não alonga automaticamente propostas de uma análise antiga: inicie uma nova análise com planejamento automático.

**Encurtar silêncios longos** combina Silero VAD local, baixo volume e timestamps de palavras. Só remove o interior de um intervalo sem voz e quieto confirmado, entre palavras inteiras, mantendo margens. Respirações curtas não são alvo. Sem confirmação no áudio, preserva a pausa e informa o motivo. **Preservar todas as pausas** desativa a redução. O EDL registra intervalos originais removidos e a nova linha do tempo; as legendas são remapeadas. Na revisão, **Revisar silêncios removidos** mostra as junções e permite ouvir o original próximo delas. A aprovação audiovisual permanece obrigatória.

Durante a análise, o painel **Análise do Gemini** mostra os resumos que a API envia, por janela e tentativa, e os eventos do aplicativo. Temas e propostas da análise atual aparecem no painel; os cortes finais ficam na área de revisão. O texto do modelo é apresentado como texto, sem executar HTML. Registros técnicos ficam em `.autoclip/jobs/<id>/analysis-events.jsonl` para diagnóstico interno; não há botão, seletor ou modal de histórico na interface. Desativar a exibição nas configurações vale para novas análises. Análise reaproveitada do cache é identificada e não inventa novos resumos ou solicitações.

A integração usa `generate_content_stream`, `include_thoughts` quando `models.get().thinking` confirma suporte, e separa partes marcadas `thought` do JSON final. Para modelos textuais compatíveis da série 2.5, o motor usa orçamento de pensamento de 2.048 tokens; para a série 3 compatível, usa nível baixo. Mostrar ou ocultar resumos não altera essa política. Pensamento pode consumir mais tokens; as chamadas são dimensionadas automaticamente para novas tarefas da interface; tentativas por falha continuam limitadas. A API disponibiliza resumos, não pensamento interno completo; disponibilidade e conteúdo dependem do modelo. Consulta de capacidade tem timeout próprio e não gera conteúdo. Referências: [thinking e resumos](https://ai.google.dev/gemini-api/docs/generate-content/thinking#thought-summaries), [saídas estruturadas](https://ai.google.dev/gemini-api/docs/structured-output).

## Preparação em outra instalação — para desenvolvimento

Python3.12 e FFmpeg/libass/libx264 são necessários. Instale o lock Python no venv e o projeto editable com extras desktop; em `desktop`, `npm ci` e `npm run build`. Execute `scripts/create_shortcut.ps1` para gerar o atalho. O modelo ASR e as licenças de distribuição são provisionados separadamente. Logs ficam em `.autoclip`, ignorados no Git; não envie credenciais ou mídia junto com logs.

## Validação

Testes automatizados do provedor usam fixtures. A conexão real ao catálogo foi validada separadamente, sem gerar conteúdo. A seleção real salva contém 19 propostas; a validação desta interface não requer novas chamadas Gemini. Consulte `docs/frontend-progress.md` e `poc-results/frontend/` para evidência de testes/startup e os limites da inspeção visual.


### Chamadas automáticas e compatibilidade

A interface não expõe limite de tentativas nem checkbox de envio de texto. O limite antigo salvo nas configurações não restringe novas análises da interface. Trabalhos antigos e seus logs são preservados. Clientes CLI/API que enviam explicitamente `max_calls` ainda usam limite manual; a CLI conserva suas opções. A contagem real continua na sidebar e nos registros técnicos internos. O cancelamento interrompe a sequência. Nenhuma falha autoriza uma repetição infinita.


### Painel equilibrado e leitura da análise

A visão geral divide vídeo e painel em duas colunas iguais; abaixo de 1000 px, usa uma coluna. As etapas automáticas e ações humanas ficam em uma grade compacta. A visão geral mostra um resumo; a aba Análise contém temas, propostas e os resumos da API. O painel mantém o trabalho ativo ou mais recente por data, independentemente da ordem de atualização. Resumos já recebidos não desaparecem quando o lote de eventos consultado avança.

O resumo acompanha novas mensagens automaticamente. Rolar para cima ou usar **Pausar acompanhamento** suspende o movimento; **Acompanhar atualizações** volta ao fim. A barra fica oculta, mas mouse, toque e teclado continuam disponíveis. Os registros técnicos permanecem internos, sem navegação por análises antigas na interface.

**Janela de análise:** intervalo de tempo da transcrição enviado por solicitação; 600 segundos correspondem a 10 minutos de conteúdo original. O motor usa sobreposição de 30 segundos nas divisões para preservar contexto. **Máximo de caracteres:** teto aproximado do texto com IDs de palavras em cada janela; textos densos são subdivididos mesmo dentro do intervalo de tempo. Não inclui todo o prompt e não equivale a tokens ou à capacidade exata do modelo. Valores maiores dão mais contexto por chamada; menores reduzem o tamanho de cada solicitação e podem aumentar o número de chamadas. Nenhum define a duração dos cortes. Os padrões 600 s / 60.000 caracteres podem ser mantidos; controles ficam em ajustes avançados.

Referências de UX consultadas antes da alteração: [NN/g — visibilidade do estado](https://www.nngroup.com/articles/visibility-system-status/), [W3C — status acessíveis](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA22.html), [W3C — pausa da rolagem automática](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR33).


### Recuperação da análise Gemini

Cada janela recebe a transcrição completa como contexto global, sem IDs fora da janela elegível para cortes. Não há mais a regra de três propostas por janela no prompt. A duração e a integridade continuam verificadas pelo motor; a seleção final ainda aplica suas regras de sobreposição e quantidade configurada.

O tempo padrão por solicitação passa de 60 para 180 segundos (com cancelamento e watchdog do processo). O processamento de pensamento é limitado independentemente da visibilidade dos resumos. Resposta com MAX_TOKENS é classificada como PROVIDER_OUTPUT_TRUNCATED; timeout como PROVIDER_TIMEOUT. Resumos nunca são aceitos como JSON final.

Respostas completas e validadas são gravadas atomicamente em work/analysis-checkpoints. Chaves incluem transcrição, modelo, prompt, janela, schema e código da integração; digest e referências são conferidos ao reutilizar. Respostas truncadas, inválidas e resumos parciais não viram checkpoints. Alterar modelo, texto, duração ou política invalida os checkpoints correspondentes. Novas análises retomam as janelas compatíveis concluídas e contam somente chamadas novas no trabalho atual, preservando os hashes/proveniência das anteriores. Antes da chamada, o motor verifica o orçamento para as janelas restantes, não para todas as janelas originais.

O botão **Continuar análise** inicia esse fluxo quando uma tarefa foi interrompida. Uma análise completa só é publicada após cobertura de todas as palavras. Falhas antigas na primeira janela não possuem resultados validados para recuperar.

Referência da política: [Gemini thinking — budgets e limites de saída](https://ai.google.dev/gemini-api/docs/generate-content/thinking#thinking-budgets).


### Respostas compactas e avisos atuais

Evidências dos temas/candidatos e listas curtas de contexto têm até8IDs cada. O início e o fim continuam definindo o trecho contínuo inteiro; palavras internas não são descartadas por não aparecerem nas evidências. Justificativas/descrições são concisas e os limites de strings são validados localmente. A telemetria separa tokens de pensamento, saída e tamanho de JSON truncado. O painel mostra erros da tarefa atual; um last-error.json antigo não é reapresentado durante outra tarefa ou após sua conclusão.

A validação real de12/10/2026 concluiu o vídeo com7janelas/19propostas, usando11/28tentativas no total incluindo diagnósticos. Veja poc-results/frontend/real-gemini-recovery.md para evidência e limites da validação. Gerar prévias continua manual.


### Análise, seleção e geração por corte

As abas são **Visão geral**, **Transcrição**, **Análise** e **Cortes**. Na Análise, filtre por tema ou busque na fala/justificativa. Ouça o trecho com ou sem 15 segundos de contexto. A reprodução do original independe de gerar MP4. Dados parciais mostram somente janelas validadas da tarefa atual; a geração exige a análise completa. O agrupamento usa rótulos equivalentes por normalização, conservando IDs e evidências; temas semelhantes com nomes diferentes permanecem separados.

A seleção é persistida em `analysis-selection.json`, vinculada ao hash da análise. O motor recusa uma seleção antiga ou inelegível. A escolha manual pode ultrapassar três propostas e mantém versões sobrepostas, com aviso. O comportamento automático antigo da CLI continua limitado pela sua configuração. As verificações de duração (20–máximo configurado) e flags editoriais continuam obrigatórias.

**Gerar prévias** consome a análise salva, sem nova chamada ao Gemini. A fila mostra edição, pausas, legendas, codificação e verificação. Percentuais usam `out_time_us` do FFmpeg sobre a duração efetiva do EDL; 100% codificado ainda aguarda QA. As demais fases mostram atividade e tempo decorrido, sem ETA. Cada corte tecnicamente válido aparece imediatamente para revisão; falhas ficam localizadas. **Continuar prévias pendentes** usa o snapshot do lote, excluindo itens já prontos.

A aba Cortes possui filtros **Em geração**, **Para revisar**, **Aprovados** e **Exportados**. É possível consultar e aprovar uma prévia pronta enquanto outras são geradas; exportação e exclusão aguardam o fim da tarefa. Uma nova receita de apresentação cria outra revisão e preserva prévias/aprovações anteriores. Aprovar continua exigindo os cinco critérios e fingerprint da revisão.

Novas prévias usam recorte **9:16, 1080×1920**, com acompanhamento facial local e legendas gravadas. Não há fundo borrado ou sobreposição horizontal. Sem detecção confiável, o recorte usa o centro. O original permanece intacto. Prévias antigas conservam seu formato; gere uma nova revisão para obter o novo enquadramento.

O tema global é claro, com preto/roxo, bordas visíveis, controles quadrados e foco contrastante. Em telas estreitas a análise empilha os painéis; as quatro abas permanecem acessíveis. Nenhum histórico de falhas foi adicionado.


### Legendas em maiúsculas

Novas prévias usam Montserrat ExtraBold incluída no pacote sob SIL OFL 1.1, sem instalação manual. O texto aparece em maiúsculas, em grupos de até três palavras: palavra falada em `#FFCC00`, demais em branco, com contorno preto espesso. A transcrição original mantém sua grafia e timestamps. Intervalos sobrepostos do ASR são limitados apenas na apresentação ASS para evitar duas legendas simultâneas. SRT permanece editável.

Prévias existentes permanecem intactas; gere uma nova revisão para aplicar o estilo. A mudança não exige nova análise Gemini. Evidência técnica: `poc-results/frontend/bold-caption-style-validation.json` e `bold-caption-style-frame.jpg`; amostra real de 3,36 segundos, sem validação editorial de um corte completo.


### Acompanhamento facial local

Novas prévias usam MediaPipe Face Detector / BlazeFace short-range em CPU, modelo versionado incluído sob Apache 2.0. A etapa **Acompanhando rosto** tem progresso por tempo do corte. Quadros reduzidos são amostrados a 2 fps; o FFmpeg interpola horizontalmente a trajetória no vídeo 9:16 a 30 fps. Não há zoom ou blur. Legendas e áudio seguem o EDL original.

O rosto inicial é o maior com confiança suficiente; depois a seleção prioriza proximidade espacial para reduzir trocas. Zona de tolerância de 2% da largura, suavização temporal e velocidade máxima de 18% da largura/segundo reduzem tremores. Perdas de até um segundo mantêm a posição; depois o recorte retorna suavemente ao centro. Nas bordas, o recorte é limitado ao quadro. Isso não identifica pessoas ou determina quem está falando; múltiplos rostos, perfis, mudanças bruscas de cena e movimentos rápidos exigem revisão.

`crop.json` guarda posições em tempo de saída, detecções e hash do modelo, vinculado à revisão. A etapa possui cache incluindo fonte, EDL, configuração, modelo e versões do runtime. Modelo/runtime ausente ou nenhum rosto detectado resulta em recorte central e motivo registrado. Falhas de decodificação não publicam resultados parciais. `reframe.enabled=false` mantém o recorte central pela CLI/configuração. Prévias existentes são preservadas; gerar novamente cria nova revisão sem nova análise Gemini.

Referências: https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/python e o model card registrado em `engine/assets/models/UPSTREAM.json`. Evidência real curta: `poc-results/frontend/face-tracking-validation.json`; isso não substitui a revisão de um corte completo.


### Falhas de importação e visão geral

A visão geral prioriza **Preparar seus cortes**. O vídeo original é uma miniatura com controles no canto superior direito do cabeçalho. Etapas 1–3 ficam em Preparação automática; 4–7 em Seleção e entrega. A transcrição continua com seu próprio player para navegação por timestamps.

Falhas de importação interrompem a barra e deixam as etapas seguintes pendentes. A biblioteca e o projeto derivam o estado da tarefa mais recente. O erro aparece junto à etapa afetada. **Tentar novamente** reaproveita a entrada e mantém o fluxo automático; **Usar arquivo local** escolhe outro arquivo pelo seletor nativo e continua no mesmo projeto antes de uma fonte ter sido importada. A fonte de projetos já importados não pode ser substituída por retry. Cancelar o seletor não mostra uma confirmação de sucesso.

Erros do YouTube são classificados sem expor logs brutos: bloqueio de autenticação/bot, limite HTTP 429 e indisponibilidade genérica. Falhas antigas SOURCE_UNAVAILABLE também são classificadas na leitura de seus logs locais. Não há bypass de CAPTCHA, leitura automática de cookies ou repetição ilimitada. Link bloqueado pode continuar falhando; arquivo local é a alternativa. A publicação de source.json pela interface ocorre somente após validação de vídeo e áudio.

Endpoint compatível: POST /api/v1/jobs/{id}/resume aceita opcionalmente {"source_input":"caminho local"}; requests antigos sem body continuam válidos.


### Toasts globais

Avisos transitórios passam por `desktop/src/notifications.ts` e um único `AppToaster`, baseado em Vue Sonner 2.0.9 (MIT). Posição: topo central; até três toasts visíveis, botão de fechar, erros por 9 segundos, avisos por 7 e confirmações por 4,5. O visual mantém bordas quadradas, sombra sólida e roxo; erros têm sinalização vermelha. Alt+T foca a área de avisos, que possui anúncio acessível. A biblioteca pausa o fechamento durante interação.

O polling notifica transições terminais de tarefas e falhas individuais de cortes uma vez. O histórico inicial não dispara uma fila de falhas antigas. Ao abrir um projeto que precisa de atenção, sua falha atual pode aparecer; **Ver motivo da falha** reabre o toast explicitamente. Estados das etapas, critérios editoriais e ações de recuperação continuam no fluxo. Banners de sucesso/erro foram removidos das páginas, formulários e painéis.

Um único host acompanha o dialog nativo aberto por Teleport e retorna ao body ao fechar. Assim o toast participa da camada superior do navegador e continua visível sobre o backdrop, sem criar um toaster por janela. Testes cobrem o erro de ação com dialog aberto, fechamento do dialog, Alt+T, deduplicação e falha de corte durante lote ativo.

Referências: https://github.com/xiaoluoboding/vue-sonner e https://ui.shadcn.com/docs/components/radix/sonner.
