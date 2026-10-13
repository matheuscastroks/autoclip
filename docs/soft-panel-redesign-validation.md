# Validação do redesign com painéis suaves

Direção aprovada: painéis suaves inspirados na referência, mantendo roxo como destaque.

## Entrega

- Navegação superior compacta; informações de sessão e motor local em um menu contextual.
- Painéis claros, bordas discretas, cantos arredondados e sombras suaves em todas as áreas existentes.
- Tabelas, formulários, select personalizado, abas e toast alinhados ao mesmo sistema visual.
- Cortes em tabela à esquerda e player 9:16 à direita, preservando seleção, revisão e exportação.
- Estado de análise com falha identificado como “precisa de atenção”, com orientação quando não há propostas.
- Um único botão de novo projeto por tela.
- Tokens, layouts e tema consolidados, substituindo quatro folhas de estilo antigas.

## Evidências

- Vitest: 13 arquivos, 65 testes aprovados.
- Build Vue/TypeScript aprovado.
- Build local Tauri aprovado, incluindo os assets atualizados.
- Navegador: projetos, configurações, análise e cortes inspecionados em 1366×768; biblioteca também em 1000×680, sem transbordamento horizontal.
- Player em 1366×768 com cerca de 304×540 pixels. Após rolagem, topo do player em 80px, abaixo do cabeçalho de 64px.
- Foco de teclado roxo com contraste reforçado; select fecha com Escape.
- Capturas em `poc-results/frontend/soft-library.png`, `soft-settings.png` e `soft-cuts.png`.

Nenhuma nova análise, renderização ou chamada a provedor foi iniciada para esta validação. O processamento existente do usuário foi preservado.

A inspeção visual foi feita no navegador. O binário Tauri foi compilado; sua inspeção visual nativa permanece pendente porque a automação de aplicativos nativos está indisponível nesta sessão.
