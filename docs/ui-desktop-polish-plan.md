# Plano de refinamento da UI desktop

Data: 12/10/2026. Estado: proposta para revisão; implementação posterior.

## Objetivo e escopo

Refinar a interface brutalista roxa para uso diário no desktop: controles com profundidade e pressão física, superfícies neutras frias, organização clara e acompanhamento do projeto inteiro sem terminal. O usuário pediu planejamento antes da implementação. Nenhum código do produto é alterado nesta etapa.

As referências fornecidas orientam bordas fortes, recortes retos, hierarquia tipográfica, sombras duras e blocos de ação. As referências mobile serão adaptadas à densidade e largura desktop. Roxo permanece a identidade aprovada; amarelo, verde-lima, fundos bege, texturas de quadrinhos e elementos promocionais das referências não serão copiados.

## Diagnóstico verificado no código

- `tokens.css`: canvas #f7f6f1, superfície auxiliar #eeede6 e texto secundário com tonalidade quente.
- `brutalist.css`: botão principal e Novo projeto possuem sombra de 3 px; secundários ficam sem sombra. O estado pressionado move 1 px e mantém a sombra original.
- Navegação, ícones, abas, temas e propostas usam regras distintas para estados de interação.
- A biblioteca apresenta Projeto, Duração e Estado; atualização e existência de análise estão disponíveis no contrato mas não são exibidas como colunas.
- Configuração local/modelo está à esquerda; chave e validação estão à direita. A ordem visual não corresponde claramente à sequência chave → catálogo → seleção do modelo.
- A preparação já organiza sete etapas e mantém vídeo pequeno no canto direito. Preservar esse avanço e refinar hierarquia e espaços.
- Há estilos sobrepostos em styles.css/brutalist.css; consolidar por componente gradualmente para evitar regressões.

Diagnóstico por leitura de código e referências. Auditoria visual do app em execução ainda será realizada antes de alterar os layouts; não foi concluída nesta etapa.

## Direção recomendada

Alternativas: (A) corrigir apenas cores/botões, com menor esforço mas mantendo problemas de jornada; (B) refinar o sistema visual e as jornadas existentes em fases; (C) reestruturar toda a navegação, com maior risco e migração desnecessária neste momento. Recomendação: B, preservando Vue e o motor atual.

### Superfícies e hierarquia

| Papel | Proposta |
|---|---|
| Fundo geral | #FAFAFA |
| Painéis e formulários | #FFFFFF |
| Cabeçalhos e áreas auxiliares | #EEEEEE |
| Texto, bordas e sombra dura | #111111 |
| Texto secundário | #595959 |
| Ação principal | Roxo #6D28D9, texto branco |
| Ação secundária | Lavanda #EDE9FE, texto #111111 |
| Erro / ação destrutiva | Variante vermelha específica; manter significado independente do roxo |

Usar uma ação principal por grupo funcional. Não transformar toda a tela em blocos preenchidos. Texto de leitura em caixa normal; títulos e rótulos fortes com uso seletivo de maiúsculas. Preservar fonte de legenda dos vídeos separada da tipografia do app.

### Botões e profundidade

- Principal: borda 2 px, sombra preta 4 px × 4 px, fundo roxo.
- Secundário: mesma construção física, fundo lavanda, sombra 3 px × 3 px.
- Ícones: dimensão consistente, nome acessível e sombra menor (2 px); ações dentro de campos devem caber sem mudar sua altura.
- Repouso: elevado; hover: mudança leve de superfície; pressão: deslocamento exatamente igual à sombra e sombra zero; soltar retorna ao repouso. O conteúdo vizinho não se move.
- Transição sugerida de 90–120 ms; validação de sensação no desktop antes de fixar o valor.
- Foco por teclado sempre visível, independente da sombra. Enter/Espaço recebem feedback equivalente sem mudar semântica ou disparar ações duas vezes.
- Desabilitado: aparência distinta, sem elevação/hover interativo; carregando: largura estável e texto específico da operação.
- Abas, filtros e seleção de temas: profundidade menor, selecionado com aparência encaixada persistente. Diferenciar seleção de pressão momentânea.
- Links dentro de textos não precisam virar blocos; recebem feedback discreto consistente. Cards informativos não parecem botões.

Criar um componente compartilhado para ações (variantes principal, secundária, destrutiva e ícone), preservando type, disabled, eventos, atributos acessíveis e seletores dos testes. Inventariar todos os controles antes da migração para não esquecer fechamentos de diálogos, lixeira e controles de seleção.

### Sidebar e transições

Sidebar com largura inicial de referência de 216–232 px, ajustada na auditoria de 1366 px. Separador preto e relevo discreto interno; sombra não pode invadir nem reduzir a área de trabalho. Navegação selecionada encaixada, ação Novo projeto elevada. Área inferior com situação dos recursos e acesso às configurações, sem inserir indicadores fictícios.

Trocas de tela/aba: opacidade e deslocamento de até 4 px em 140–180 ms. Diálogos podem usar entrada curta semelhante. Preservar vídeo, seleção, posição útil de rolagem e polling; atualizar progresso não dispara animação de tela nem remonta players. Respeitar redução de movimento do sistema, removendo deslocamentos e mantendo feedback de estado.

## Jornada desktop

### 1. Primeira configuração e prontidão

Mostrar configuração inicial quando os requisitos estiverem incompletos, com acesso posterior em Configurações. Três grupos ordenados: recursos locais (Whisper e FFmpeg/ffprobe), conexão Gemini (inserir/salvar/testar chave), modelo e preferências (catálogo e duração/pausas).

Cada grupo mostra não configurado, verificando, disponível ou problema com ação corretiva. Chave salva não significa conexão validada; consulta de catálogo não significa cota de geração disponível. Oferecer caminho para selecionar os arquivos/pastas existentes, com rótulos compreensíveis e detalhes técnicos sob expansão. Download automático de modelos não faz parte deste plano.

Preferências avançadas ficam recolhidas. Antes de iniciar a cadeia automática, apresentar o requisito faltante e atalho exato para corrigi-lo. A possibilidade de importar sem Gemini precisa ser conciliada com o agendamento existente: não bloquear importação local desnecessariamente nem prometer análise automática sem configuração válida.

### 2. Novo projeto

Diálogo com nome, origem URL/arquivo e resumo do que ocorrerá automaticamente. Estado dos recursos visível, campos alinhados, ação final clara. Preservar valores em erros. Progresso acompanha o projeto após criação, sem obrigar manter diálogo aberto. Nenhum checkbox de autorização adicional.

### 3. Biblioteca de projetos

| Coluna proposta | Informação e origem |
|---|---|
| Projeto | Capa, título e fonte; dados existentes |
| Duração | Duração original; dado existente |
| Etapa / estado | Importando, transcrevendo, analisando, aguardando seleção, gerando, revisão ou exportado; requer agregar jobs e artefatos |
| Cortes | Propostos, selecionados, gerados; requer resumo de análise/seleção/revisões |
| Atualizado | Timestamp existente, com data completa disponível |
| Ação | Abrir/continuar e menu de ações; exclusão conforme bloqueios e lixeira atuais |

Em 1366 px, reduzir detalhes secundários e juntar contagens de cortes numa célula; não esconder título/estado/ação. Em 1920 px, mostrar contagens separadas se houver espaço. Contar candidatos únicos e revisões vigentes, sem inflar números por múltiplas renderizações. Distinguir zero de não disponível. Contagem exportada deve ter fonte real verificável antes de ser exibida.

Filtros por estado, busca e ordenação por atualização/nome. Uma ação explícita de abrir projeto evita botão de linha contendo outros botões; manter clique na linha somente se a semântica e teclado forem consistentes. Distinguir a causa do problema da etapa atual; não manter Importando após falha terminal.

Criar contrato de resumo por projeto no backend para contagens/etapa, evitando uma requisição por linha e leitura de toda a transcrição. Incluir dados de fila em execução sem inventar percentuais onde a etapa não fornece total.

### 4. Preparar seus cortes

Manter fonte em miniatura no canto superior direito, preparação como foco. Etapas automáticas 1–3 e participação do usuário 4–7 visualmente distintas. Cada etapa: título, estado, resumo e ação contextual. Etapa ativa com progresso real quando disponível; atividade textual quando não houver total. Concluídas compactas; pendentes explicam pré-requisito.

Destacar próxima ação: escolher trechos, gerar prévias, revisar ou exportar. Falha oferece tentar novamente/continuar/substituir fonte conforme recuperação suportada. Toast concentra notificações; estado persistente da etapa mantém o diagnóstico e ação de recuperação sem repetir banners de erro.

### 5. Temas, seleção, revisão e exportação

Análise com temas à esquerda, propostas no centro e detalhe/preview ao lado conforme largura. Em notebook, priorizar duas áreas com detalhe acessível sem esmagar colunas. Seleção e quantidade selecionada sempre claras; gerar prévias junto ao resumo da seleção.

Revisão com lista de cortes, player vertical e painel de aprovação. Separar título de publicação, abertura do vídeo, justificativa e verificações. Área de ação visível sem cobrir conteúdo. Exportação mostra apenas itens elegíveis e destino, com resultado por corte. Novos editores de abertura/legendas não estão incluídos nesta revisão visual.

## Sequência de execução e aceite

1. **Auditoria visual e mapa da jornada:** capturar biblioteca, configurações, novo projeto, preparação, temas e revisão em 1366×768, 1440×900 e 1920×1080. Registrar recortes, excesso de rolagem, ações ambíguas e estados ausentes. Aceite: lista de problemas com tela, prioridade e proposta, sem alterar processamento.
2. **Sistema de superfícies e botões:** tokens frios, variantes físicas, foco e redução de movimento. Migrar controles por tela. Aceite: pressionar recolhe a sombra completamente; nenhum salto de layout; teclado e controles desabilitados funcionam; variantes preservam hierarquia.
3. **Estrutura desktop:** sidebar, espaços em escala 4/8/12/16/24/32, cabeçalhos, diálogos e transições. Aceite: sem rolagem horizontal da página nas resoluções-alvo; sombras e toasts não recortados; troca de abas preserva reprodução e seleção.
4. **Configuração e onboarding:** grupos em sequência e estados de prontidão com correções. Aceite: usuário consegue localizar recursos, salvar/testar chave e selecionar modelo sem terminal; estado e mensagens correspondem à verificação realmente realizada.
5. **Biblioteca e resumo do projeto:** contrato agregado, colunas, ordenação e ações. Aceite: números correspondem aos artefatos, atualizam durante execução e não contam revisões duplicadas; sem requisições individuais por linha; abertura e exclusão acessíveis por teclado.
6. **Preparação, análise e revisão:** hierarquia de etapas e ações, layouts de notebook, exportação. Aceite: usuário identifica o que está acontecendo e o próximo passo em cada estado; recuperação não perde progresso válido.
7. **Validação da jornada:** testes Vue de interação/foco/seleção, testes API do resumo, build e revisão visual por resolução. Fluxo com vídeo local: configurar → importar → transcrever → analisar → selecionar → gerar → revisar → exportar. Simular chave inválida, origem indisponível, cancelamento e retomada. Chamadas externas reais precisam de escopo de teste definido; testes de UI usam respostas simuladas.

Arquivos prováveis: desktop/src/{tokens.css,styles.css,brutalist.css,App.vue}, componentes de biblioteca/configuração/preparação/análise/revisão, novo componente de botão, types.ts e endpoints/resumo de projetos em engine/api. Alterações visuais não modificam seleção semântica, transcrição, MediaPipe ou renderização dos vídeos.

## Referências de acessibilidade consultadas

- Foco visível: https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- Redução de animações por interação: https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html

Decisões de cores, tamanhos e duração acima são propostas para este produto, não valores prescritos pelo W3C. Antes de implementação, revisar este plano e definir o primeiro lote. Prioridade recomendada: sistema visual/botões, estrutura desktop e biblioteca; depois onboarding e refinamento da jornada completa.
