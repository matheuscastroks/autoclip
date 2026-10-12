# Interface para administrar o AutoClip

Status: proposta concreta para revisão; implementação ainda não iniciada.

## Objetivo e contexto

Pedido de 12/10/2026: deixar a validação semântica Gemini pendente e avançar para uma interface que permita administrar o projeto sem terminal. Preservar o motor Python independente, contratos v1, revisão humana e processamento local. Não realizar novas chamadas Gemini durante desenvolvimento/validação da interface.

Sucesso: abrir por atalho no Windows, localizar projetos existentes, importar vídeo, configurar modelos/credencial, acompanhar ou cancelar tarefas e revisar/exportar quando existirem cortes válidos. Erros do motor precisam ter recuperação pela interface.

## Abordagem recomendada

Vue 3 + TypeScript com API FastAPI em loopback, conforme arquitetura existente. Primeiro entregar interface funcional e launcher Windows que inicia API e abre a interface por duplo clique, sem comandos do usuário. Interface servida localmente pela API; nenhum servidor remoto. Encapsulamento Tauri 2 é a próxima camada, sem reescrever Vue/API, após provisionar e validar Rust/build nativo.

Alternativa: começar pelo Tauri e empacotamento Python imediatamente. Entrega uma janela nativa desde o início, porém acrescenta toolchain e distribuição ao trabalho antes de validar o gerenciamento. Outra alternativa, painel estático sobre relatórios HTML, facilita consulta mas não atende importação, configuração e administração; descartada.

Não chamar de instalador final o launcher de desenvolvimento. O marco inicial usa os runtimes/modelos já provisionados no notebook. Empacotamento autossuficiente, licenças e instalação em máquina limpa são marcos próprios.

## Organização e aparência

Aplicativo em português, inspirado em uma mesa de edição: navegação lateral compacta, biblioteca de projetos e área de trabalho do vídeo. Superfície clara #F5F7FA, painéis #FFFFFF, texto #182334, borda #DCE3ED, ação #315FC5 e aviso #965D16. Tipografia Segoe UI instalada no Windows; tamanhos legíveis de 14–28 px. Sem fontes/CDNs remotos ou animações decorativas. Contraste, foco visível, teclado e redução de movimento.

Layout para notebook 1366×768: lateral 200 px; cabeçalho com nome e ação principal; lista em linhas com miniatura real quando disponível; detalhes do projeto com vídeo e tarefas. Revisão dedica o espaço principal ao player e contexto, com lista de cortes e transcrição adjacentes. Em janelas menores, painéis empilham e controles continuam acessíveis.

## Telas e operações

### Biblioteca

Listar projetos cadastrados, fonte, estado, duração e data. Buscar por nome e filtrar estados. Abrir, criar por arquivo/URL e importar pasta de projeto existente pelo seletor gráfico. Cadastrar sem mover/apagar a mídia original. Guardar referências no SQLite; projetos e artefatos permanecem em suas pastas.

Descoberta inicial das pastas locais existentes, inclusive `jones-manoel`, `gemini-test` e preview manual. Mostrar a transcrição existente sem repetir 47 minutos de ASR. Projetos incompletos ou formatos manuais aparecem como importação parcial; não inventar revisões compatíveis nem aprovações.

### Projeto

Mostrar original com reprodução, proveniência resumida, transcrição disponível e etapas reais. Status por etapa e avisos; sem porcentagens ou ETA inventados. Um trabalho pesado por vez no notebook. Cancelar e retomar a partir de manifests válidos; falhas conservam artefatos e exibem causa compreensível.

Controles separados: importar/transcrever, analisar com Gemini e gerar prévias. Isso exige fronteiras de execução no runner atual, que hoje executa sequencialmente até o provedor. Nunca disparar chamadas remotas ao abrir/importar um projeto. Antes de analisar: modelo, limite de tentativas, indicação de envio somente de texto e número mínimo de janelas. Todas as tentativas persistidas antes do envio, inclusive retries/repair, para não perder orçamento após interrupção.

### Revisão e exportação

Quando houver revisões válidas: reproduzir preview e original com contexto, mostrar intervalo e motivo do candidato, legendas e QA. Cinco critérios editoriais explícitos e notas; aprovação vinculada ao fingerprint existente. Rejeição disponível. Exportar somente aprovados, mostrar arquivos e abrir pasta de saída. Estado vazio honesto quando a análise falhou; preview manual permanece identificado como manual e não aprovado.

Edição gráfica de EDL/legendas, tracking facial e remoção de pausas ficam para outro marco; não adicionar controles sem ação funcional.

### Configurações

Selecionar pasta/modelo ASR local, paths FFmpeg quando diagnóstico não localizar, modelo Gemini e limite de chamadas por trabalho. Campo de chave oculto com salvar/substituir em Credential Manager; API retorna apenas presença da credencial. Nunca retornar segredo à interface, colocá-lo em localStorage ou incluí-lo no Git. Diagnóstico local de recursos; teste remoto só em ação explícita com autorização/orçamento próprio.

## Integração e armazenamento

`desktop/`: Vue/TypeScript, componentes e testes. `engine/api/`: FastAPI/serviços locais. SQLite registra id, nome, caminho, datas, configurações e jobs; EDL, ASR, revisões e manifests continuam fontes de verdade do motor. Nenhuma duplicação da lógica de análise/render no frontend.

API versionada: health/config, projetos/importação/detalhes, transcrição, jobs/start/status/cancel, revisões/decisões, exports e mídia autorizada. Jobs em subprocesso, sem bloquear API; recuperação de interrupted após reiniciar. Polling inicial de estado/eventos persistidos é suficiente; SSE futuro preserva contratos.

Escuta somente em 127.0.0.1, token de sessão, validação de Origin e sem CORS wildcard. Caminhos resolvidos e confinados a projetos registrados; mídia acessível por ids e Range requests para seek, sem endpoint de arquivo arbitrário. Importação externa somente por operação explícita. API não recebe comandos shell do browser. Segredos e argumentos de jobs separados.

Launcher verifica instância existente antes de iniciar outra; processos ocultos e logs locais. Ao abrir o atalho, basta aguardar a interface. Startup/encerramento documentados; não prometer cancelamento do job ao simplesmente fechar uma aba.

## Critérios de aceite e verificação

1. Abrir pelo atalho sem terminal; biblioteca responsiva em 1366×768.
2. Projetos existentes visíveis com transcrição/erros corretos e sem repetir inferência ou chamar Gemini.
3. Importação de arquivo com espaços/acentos; estados e falhas exibidos sem congelar navegação.
4. Salvar configuração/chave pela UI, sem segredo em respostas, storage ou logs.
5. Iniciar/cancelar/retomar tarefa local e recuperar interrupted após reinício.
6. Aprovação e exportação bloqueadas quando QA/fingerprint não autorizam; fixtures rotuladas em testes, sem fake clips na biblioteca real.
7. API testa autenticação, confinamento, importação, orçamento persistido e gate editorial. Frontend testa ações/erros importantes; QA visual e fluxo real no browser. Suite existente continua passando.
8. Commit no Git local e runbook de duplo clique; nenhum push/publicação automática.

## Pendências explícitas

Esta etapa não prova qualidade da seleção Gemini nem integridade editorial do vídeo real. Nenhuma nova chamada remota está autorizada para testes. O teste do provedor usa fixtures. Empacotamento Tauri, instalador e distribuição em máquina limpa são o marco seguinte.

Revisão da proposta: requisitos rastreados ao pedido; funcionalidades derivadas do motor existente; limites de fase explícitos; nenhum botão sem contrato; launcher separado de instalador final. Próximo artefato após aprovação: plano de implementação com tarefas e execução no repositório atual.
