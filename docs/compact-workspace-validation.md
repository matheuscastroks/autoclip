# Workspace compacto — 12/10/2026

Entrega autorizada após a proposta de configurações segmentadas, fila lateral e áreas de trabalho com altura disponível.

## Alterações

- Configurações divididas em tabs/tiles Recursos locais, Gemini e modelo, Preferências dos cortes. Valores em edição permanecem entre etapas. Whisper, FFmpeg e ffprobe compartilham uma linha no desktop; Gemini e catálogo compartilham duas áreas.
- Campos inválidos revelam sua etapa e abrem detalhes ancestrais antes de receber foco. Navegação de tiles suporta setas/Home/End.
- Visão geral e cortes compartilham sidebar de geração. Ordem: em execução, falhas, pendentes, prontas. Inclui prévias salvas disponíveis, com botão para abrir. Revisões excluídas não mantêm links de acesso. Uma versão pronta anterior pode permanecer disponível enquanto outra tentativa do mesmo candidato falha.
- Etapas numeradas em grid. Cabeçalho compacto com vídeo original de referência. Área principal e fila possuem rolagem independente; o cabeçalho da fila permanece acessível.
- Transcrição com vídeo menor e lista de falas com rolagem própria.
- Análise apresenta três passos: escolher tema, escolher trecho, conferir/selecionar. Resumos na lista são compactos; contexto e abertura completos podem ser expandidos no detalhe. Ação de selecionar fica fora da área rolável do detalhe.
- Cortes com lista à esquerda, player 9:16 e sidebar de geração à direita. Texto de publicação/contexto e revisão editorial ficam em seções próprias. Seleção externa na sidebar reseta filtro incompatível para alinhar player, título e revisão.
- Altura disponível medida a partir do DOM, com atualização no resize e limpeza de observer/listener. Em telas menores, os layouts retomam fluxo vertical para permitir acesso ao conteúdo.

## Verificação

- Suíte Vue completa: 61 testes passaram. Após refinamentos finais, testes direcionados de análise/revisão e configuração foram reexecutados. Build TypeScript/Vite aprovado.
- Regressões cobertas: dados preservados entre tiles; campo inválido oculto/avançado; ordem da fila sem mutar snapshot; prévia pronta sem job; revisão excluída; seleção externa fora do filtro; selecionar/remover proposta pelo detalhe.
- Revisão independente identificou e ajudou a corrigir os problemas de validação oculta e de alinhamento entre vídeo e revisão.
- Navegador real 1366×768: campos locais na mesma linha; página da transcrição com scrollHeight 768 e lista de 25.195 px dentro de área rolável de 368 px; visão geral e análise com scrollHeight 768; player dos cortes com razão largura/altura 0,5625 (9:16), sem contêiner horizontal excedente.
- Gemini e modelo também couberam na altura de 768 px depois do ajuste de espaços. Preferências receberam ajuda recolhível e redução adicional de padding; textos expandidos podem exigir rolagem.

Capturas: poc-results/frontend/compact-settings.png, compact-preparation.png, compact-transcript.png e compact-cuts.png. O projeto real mantém falhas de renderização anteriores; elas não foram retratadas como sucesso. Esta entrega altera a UI, não os arquivos MP4 nem as decisões do modelo.

Não foram iniciadas chamadas de geração, transcrição ou renderização. O motor não foi reiniciado. O teste visual usou a fonte, análise e prévias existentes. Validação visual exaustiva de todos os estados e resoluções permanece fora da evidência desta entrega.
