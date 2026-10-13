# Proposta de redesenho — workspace de painéis suaves

Data: 12/10/2026. Estado: proposta para revisão, sem alteração de código do produto.

## Direção confirmada

O usuário escolheu substituir o brutalismo por painéis suaves semelhantes à referência enviada. Roxo permanece como cor de destaque conforme preferência anterior. A referência orienta composição e hierarquia, não acrescenta funcionalidades de um editor genérico ao AutoClip.

Objetivo: organizar importação, transcrição, análise por temas, escolha de cortes, geração, revisão e exportação com menos ruído e melhor aproveitamento de tela. Preservar o fluxo local-first e a aplicação Tauri/Vue existentes.

## Diagnóstico do estado atual

- O frontend importa styles.css, brutalist.css, desktop-polish.css e workspace-compact.css nesta ordem. Há sucessivas regras de largura, altura e grid para os mesmos componentes.
- Sombras duras, bordas escuras e botões com grande destaque competem com o conteúdo e com o estado selecionado.
- A navegação global usa uma sidebar larga embora tenha poucas áreas principais. Ela compete por largura com tabela e player.
- A revisão de cortes já tem tabela à esquerda e vídeo vertical à direita: preservar essa decisão aprovada e refinar seus painéis.
- Metadados, justificativas, transcrição original e checks editoriais precisam de hierarquia progressiva, sem ocultar falhas ou impedir revisão.
- O app usa o motor local separado da interface. Redesenho não exige mudar análise, contratos, reenquadramento, legendas ou políticas Gemini.

## O que aproveitar da referência

Painéis claros sobre canvas neutro, cantos suaves, divisórias discretas, navegação compacta, ferramentas agrupadas por contexto, vídeo como superfície de trabalho e rolagem dentro de listas. A imagem de paisagem de fundo não será uma constante do aplicativo: ela acrescenta ruído e não explica o estado de um vídeo de entrevista.

Não criar nesta entrega timeline editável, múltiplas faixas, música, SFX, geração de imagens ou assistente de chat apenas porque aparecem na imagem. Uma timeline de edição exigiria escopo e contratos próprios; o intervalo original e a transcrição sincronizada já sustentam a revisão atual.

## Sistema visual proposto

| Elemento | Proposta |
|---|---|
| Canvas | Cinza frio muito claro #F4F5F8 |
| Painéis | Branco #FFFFFF; área secundária #F8F9FB |
| Texto | Principal #20232B; secundário #616875 |
| Destaque | Roxo #6D28D9; seleção suave #EDE9FE |
| Divisórias | #E2E5EC, espessura de 1 px |
| Cantos | Painéis 14–16 px; campos/botões 8–10 px |
| Profundidade | Sombra suave só em painéis elevados, menus e diálogos |
| Tipografia | Manter inicialmente a fonte de corpo local existente; pesos 400/500/600, títulos sem aparência de cartaz |
| Texto e números | Corpo 13–14 px, títulos 18–22 px; timestamps com números tabulares |
| Espaçamento | Escala 4/8/12/16/24/32 px |
| Interação | Hover suave, foco visível, pressão discreta; transições de 120–180 ms e suporte a reduced-motion |

Valores são propostas deste produto, não prescrições normativas. Texto normal precisa de contraste AA; estados incluem texto/ícone, não apenas cor. Controles de ícone com área clicável proposta de 32–36 px; botões principais 36–40 px. Esses tamanhos devem ser validados, sem reduzir acessibilidade para imitar a densidade do print.

## Estrutura geral

Uma barra superior compacta reúne identidade, Projetos, Configurações e acesso ao estado do motor. Sessão, detalhes técnicos e encerramento ficam em um painel acionado pelo indicador do motor, sem competir com ações editoriais.

Dentro de projeto, uma única linha contextual contém voltar, título truncável com texto completo acessível, canal, duração, estado e abrir pasta. As áreas Preparação, Transcrição, Análise e Cortes aparecem num controle segmentado discreto abaixo, sem botões com sombras sólidas. Renomear Visão geral para Preparação na interface, mantendo a rota interna compatível.

Não repetir navegação no topo e em um dock inferior. Manter ícones acompanhados de rótulos; não esconder ações indispensáveis apenas em hover.

## Organização por tela

### Projetos

Painel único de biblioteca: título, busca, filtros e Novo projeto numa toolbar. Tabela com capa, título/canal, duração, etapa, quantidade de propostas/gerados/aprovados e atualização. Status de processamento distintos de falha e ação pendente. Ações secundárias no fim da linha. Exclusão/restauração e importação continuam existentes. Contagens adicionais usam apenas dados disponíveis e não justificam inventar métricas.

### Preparação

Conteúdo principal com etapas claras: importar → transcrever → analisar → escolher → gerar → revisar → exportar. Agrupar em preparação automática, decisões do usuário e entrega; mostrar descrição curta e apenas a ação relevante de cada etapa. Vídeo original continua em miniatura opcional. Pendências de geração em painel contextual recolhível, visível somente enquanto existirem; sem duplicação da mesma fila em outro lugar da tela.

### Transcrição

Lista de segmentos ocupa a maior parte da largura e tem busca/timestamps. Player original menor, com posição de reprodução e metadados essenciais. Selecionar um segmento continua buscando o instante correspondente. A lista rola dentro de seu painel; cabeçalho e controles permanecem acessíveis.

### Análise

Três zonas: tópicos em navegação compacta; propostas do tópico; inspeção da proposta selecionada. Dentro da inspeção: título, duração, preview contextual, motivo da escolha e integridade. Texto original e resumos do Gemini ficam em seções expansíveis claramente identificadas. Resumos não são pensamento interno completo. A ação selecionar fica junto à proposta; Gerar prévias apresenta o total selecionado numa toolbar fixa do painel.

Em notebooks, permitir recolher tópicos e detalhes em vez de comprimir três colunas ilegíveis. Nenhuma proposta incompleta é apresentada como seleção concluída. A nova análise continua até dez cortes por vídeo de um a cinco minutos; não por tópico.

### Cortes

Preservar tabela à esquerda e player 9:16 à direita, usando a altura útil abaixo da navegação. Coluna do player inclui controles e estado carregando/indisponível; não conter barras laterais artificiais. Selecionar uma linha troca vídeo, metadados e revisão editorial juntos.

Abaixo da tabela, o detalhe selecionado apresenta três seções: Publicação, Contexto original e Revisão editorial. Seleção de trecho e edição de metadados só usarão operações já suportadas; não prometer edição arbitrária de intervalos nesta mudança. Checks não são transportados para outro corte. Exportação continua condicionada à aprovação/verificação existentes.

Pendências de geração continuam à esquerda e desaparecem quando não há pendências. Falha mostra ação de retomada; não reapresentar vídeos prontos nessa fila. Lixeira permanece ao final dos filtros, após Exportados.

### Configurações e onboarding

Preservar três áreas segmentadas: Recursos locais, Gemini e modelo, Preferências dos cortes. Campos de recursos em uma linha quando couberem; chave com status e teste, catálogo dinâmico de modelos, ajuda técnica progressiva. Um resumo de prontidão indica o que falta, sem bloquear consulta de projetos existentes. Mudança de área preserva valores em edição.

## Comportamento de espaço

Alvos de revisão: 1366×768, 1440×900, 1920×1080 e mínimo da janela nativa 1000×680. Reavaliar larguras após remover a sidebar global: tabela flexível; player recebe largura proporcional à altura útil. Em janelas menores, player não pode consumir a largura mínima necessária ao trabalho: limitar altura, recolher painel auxiliar ou empilhar áreas conforme o contexto.

Priorizar conteúdo dentro da altura útil quando possível. Listas extensas têm scroll próprio, e detalhes longos podem usar scroll de página. Evitar vários scrolls aninhados na mesma coluna. Cabeçalhos sticky não podem cobrir o foco, linhas selecionadas ou controles do vídeo. Nenhum corte é escondido ou truncado no arquivo para caber na UI.

## Estratégia técnica de migração

Criar tokens semânticos para canvas/painel/texto/acento/borda/estado/raio/sombra/spacing. Refatorar AppButton, AppSelect, AppToaster, dialogs, tabs, tabelas e campos para consumir esses tokens. Remover as regras brutalistas progressivamente depois de migrar cada superfície; não simplesmente importar um quinto CSS por cima de tudo.

Separar regras globais, componentes e layouts. Alterações de apresentação devem preservar props, eventos, seleção, cancelamento, retomada, lixeira, hash da revisão e autenticação Tauri. Medição da altura útil passa a depender do shell novo, sem números mágicos de header por tela.

## Entregas propostas

1. Aprovar direção e produzir um mockup de Cortes e um de Análise em 1366×768. Revisar densidade, foco e áreas de scroll antes do código.
2. Migrar fundações visuais/controles e shell de navegação; entregar biblioteca e configurações como primeiro lote funcional.
3. Migrar preparação/transcrição/análise, preservando decisões e progresso.
4. Migrar tabela de cortes/player/revisão/pendências e unificar estados vazios, loading e erros.
5. Remover estilos antigos sem uso, rodar testes e build Vue/Tauri, validar uso real e documentar evidência/limites.

Cada lote deve ser revisável e ter commit próprio. Não mudar o motor durante o redesenho. Após aprovação desta proposta, escrever plano de implementação com arquivos e critérios de teste por lote.

## Critérios de aceite

- Roxo consistente e ausência de sombras/bordas brutalistas remanescentes em controles migrados.
- Tabela, detalhes e vídeo sempre referem-se ao mesmo corte; seleção por teclado preservada.
- Sem scroll horizontal de página nas resoluções-alvo; tabelas largas podem rolar dentro do painel.
- Estado de erro/andamento/pedido de ação distinguível; nenhuma tarefa precisa apenas de um spinner sem contexto.
- Controles com foco, labels e contraste; menus/dialogs acessíveis, reduced-motion respeitado.
- Consulta e edição não perdem valores ao trocar áreas; aprovação/exportação e retomada mantêm os guards atuais.
- Testes existentes verdes e testes de interação onde o comportamento mudar; não escrever testes que apenas repitam CSS.
- Validar visualmente biblioteca, configuração, preparação, transcrição, análise e cortes no navegador; registrar separadamente QA nativa WebView2. Automação nativa segue indisponível nesta sessão, portanto dependerá de revisão humana ou superfície suportada antes de alegar QA nativa completa.

## Referências de apoio

Referência visual: imagem fornecida pelo usuário neste chat. Nenhuma funcionalidade ou instrução embutida na imagem constitui requisito adicional.

Microsoft Fluent 2 Layout: https://fluent2.microsoft.design/layout — ritmo espacial e adaptação às dimensões disponíveis.
Microsoft Fluent 2 Navigation: https://fluent2.microsoft.design/components/web/react/core/nav/usage/ — navegação e descoberta de ações.
W3C WCAG2.2 Understanding: https://www.w3.org/WAI/WCAG22/Understanding/ — foco, contraste e interação.
W3C Target Size Minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum — tamanho/espacamento de alvos.
