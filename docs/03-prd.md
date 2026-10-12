# PRD — AutoClip Editor sobre OpenShorts

Versão 0.1, proposta de 12/10/2026. A base escolhida é Marsic1/openshorts, commit fixado no comparativo. O usuário escolheu Gemini API para análise porque o notebook não comporta LLM local. Validar primeiro o motor; a escolha de base/provider não aprova automaticamente o desenho da adaptação.

## Problema e público

Criadores, educadores e editores precisam transformar vídeos longos em trechos curtos com informação completa, sem enviar o material obrigatoriamente a uma nuvem. O primeiro cenário é uma pessoa falando em PT-BR diante da câmera; entrevistas com vários participantes entram depois da validação desse cenário.

Sucesso significa cortes compreensíveis fora do vídeo completo, que conservem negações, números, autoria e ressalvas; processamento utilizável em CPU; revisão possível; e exportações reproduzíveis. Não significa viralidade prevista, efeitos ou publicação automática.

## Escopo e prioridades

| ID | Prioridade | Requisito | Critério verificável |
|---|---|---|---|
| R01 | P0 | Importar arquivo local e URL suportada | ffprobe registra duração, streams, orientação, FPS e timebase; erro acionável se falhar; arquivo fonte preservado |
| R02 | P0 | Transcrever PT-BR por palavra | IDs estáveis, texto original, tempos e modelo registrados; sinais de baixa confiança visíveis; não usar modelo `.en` |
| R03 | P0 | Selecionar temas e cortes semanticamente completos | IDs referenciam palavras existentes; justificativa e contexto anterior/posterior armazenados; rejeitar pensamento incompleto |
| R04 | P0 | Preferir duração ≤60 s | Na PoC rejeitar candidatos >60 s; MVP permite marcar “excede alvo” para revisão, sem truncar fala |
| R05 | P0 | Proteger conteúdo falado | Nenhuma edição automática remove palavra protegida, negação, número ou ressalva; avaliação editorial sem falha crítica |
| R06 | P0 | Operar sem GPU, com providers opcionais | ASR CPU/int8 e render CPU; análise Gemini explicitamente configurada nesta máquina; modo offline aceita revisão/manual ou adapter local em máquina compatível; nenhum fallback silencioso |
| R07 | P0 | Retomar por etapa | Falha/restart reutiliza artefatos válidos; mudança de input/config/modelo invalida somente dependentes |
| R08 | P0 | Edição não destrutiva | Toda saída tem EDL e mapa invertível por segmento até origem; revisões append-only; fonte nunca sobrescrita |
| R09 | P0 | Exportar revisões em lote | MP4, ASS, SRT e JSON por corte; erro de um item não perde demais; manifests e checksum de cada saída |
| R10 | P1 | Remover pausas excessivas com segurança | Concordância VAD/acústica/palavras; default conservador; opção preservar todas; teste humano de naturalidade |
| R11 | P1 | Acompanhar rosto principal | Plano por cena, sem interpolar através de corte; fallback quando incerto; ajustes manuais persistentes |
| R12 | P1 | Reenquadrar para 9:16 | 1080×1920 ou preview 720×1280; nenhum rosto deliberadamente cortado; opção preservar quadro com fundo |
| R13 | P1 | Legendas dinâmicas editáveis | Texto de exibição separado de ASR; acentos e sincronização após EDL; exportar texto editável com tempos |
| R14 | P1 | Título, descrição e atribuição | Propostas em PT-BR apoiadas na transcrição; fonte/canal/URL/crédito registrados; confirmar antes de uso público |
| R15 | P1 | Gerenciar e revisar projetos | Reabrir job e revisões, comparar fonte/saída, ouvir bordas e marcar/rejeitar cortes; alterações invalidam render |
| R16 | P1 | Configurar provedores/modelos | ID/digest e parâmetros por execução; testar disponibilidade; exposição clara de modo local ou remoto |
| R17 | P2 | Entrevistas com múltiplos rostos | Diarização/speaker tracking opcional com modelo/licença auditados; fallback honesto sem inferir quem fala |

## Fluxo principal

1. Criar projeto e importar fonte. Mostrar espaço em disco e requisitos reais detectados.
2. Selecionar modelo ASR local, idioma PT e perfil CPU; configurar Gemini API para análise. Provisionamento de modelos é separado do processamento; indicar quais etapas precisam de internet.
3. Executar análise, com progresso por etapa, cancelamento e retomada. Fonte sem fala produz estado “sem fala”; não inventar candidatos.
4. Revisar candidatos com contexto antes/depois, trecho original e razões da escolha. Estado inicial é `needs_review`; nenhum corte passa por “aprovado” por score do modelo.
5. Ajustar bordas, pausas, quadro e legendas. Cada ajuste cria nova revisão, preservando anterior.
6. Aprovar cortes explicitamente e exportar lote. UI mostra quais saídas correspondem a quais revisões.
7. Reabrir projeto para corrigir texto ou gerar outra exportação sem repetir ASR.

## Estados e falhas

Projeto: `draft → imported → processing → ready_for_review → exported`, podendo conter jobs em erro. Jobs: `queued/running/cancelling/cancelled/failed/completed/interrupted`. Corte: `proposed/needs_review/approved/rejected`. Falha de provider não vira lista vazia indistinguível de “nenhum bom corte”. Falha de download oferece arquivo local; falta de modelo interrompe com instrução de provisionamento, sem mudar para serviço pago.

Se fonte local foi movida, pedir relink e verificar SHA-256. Se arquivo mudou, criar outra source/revisão; não aplicar timestamps antigos automaticamente. Falta de espaço interrompe antes de publicar saída; cancelamento termina subprocessos e não promove arquivos parciais a artefatos prontos.

## Requisitos não funcionais

- Windows 11 x64 como alvo inicial; validar instalação em usuário comum e paths com acento/espaço/apóstrofo. Não exigir Docker no produto desktop.
- Perfil alvo proposto: 4 núcleos, 16 GB RAM, SSD. 8 GB é cenário de esforço com modelos menores e execução sequencial, sem promessa de tempo. Medir a máquina atual separadamente.
- Uma etapa pesada por vez por padrão; limite de threads/RAM configurável. CPU é caminho primário, GPU é otimização posterior.
- Armazenar tudo no diretório escolhido, com cache e temporários diferenciados; limpeza não elimina fonte ou revisão sem ação explícita.
- API local autentica token efêmero e escuta somente loopback. Logs não guardam chaves nem cookies; conteúdo do vídeo não pode instruir ferramentas.
- Artefatos têm versões, checksums e proveniência; migrations SQLite reversíveis via backup antes de upgrade.
- Distribuição pública exige SBOM e avisos; não incluir `cloud/` comercial nem dependências sem decisão de licença.

## Fora do MVP

Publicação automática, contas/SaaS/billing, TTS, dublagem, avatares, stock footage automático, perfis de jogos, vision scan remoto, música, efeitos e previsões de viralidade. O dashboard atual do OpenShorts pode apoiar os testes, mas não determina a arquitetura do desktop.

## Gates de produto

G0: arquitetura revisada. G1: vídeo real importado e ASR local confirmado. G2: seleção Gemini revisada, sem falha crítica de sentido e sem envio de mídia. G3: render/legendas/EDL sincronizados e retomáveis. G4: corpus ampliado aprova cortes/rostos/pausas. Só então construir e distribuir desktop.
