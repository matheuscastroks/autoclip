# Contratos da área de análise e geração

Versão dos documentos JSON: `1.0`. Todos os endpoints permanecem locais e autenticados.

## Leitura editorial

`GET /api/v1/projects/{id}/analysis` retorna estado (`not_started`, `running`, `partial`, `completed`, `failed`, `cancelled`), `job_id`, `analysis_hash`, modelo, janelas concluídas/total, `topic_groups` e `proposals`.

Cada grupo conserva IDs dos temas, resumos e evidências. Normalização de caixa, acentos e espaços agrupa somente rótulos equivalentes; não elimina negações nem faz agrupamento semântico por aproximação.

Cada proposta inclui `candidate_id`, `topic_ids`, `group_id`, título, justificativa, limites/duração em microssegundos, IDs das palavras, evidências, flags editoriais, avisos, elegibilidade, motivos e fala/contexto original. O tempo é calculado pelas palavras; a evidência compacta não encurta a fala.

A análise completa é lida de `analysis.json` e deve cobrir a transcrição atual. Durante uma nova tarefa, somente seu snapshot atômico `analysis-preview.json` é apresentado. Esse snapshot agrega janelas validadas, não resumos de pensamento ou uma cauda de eventos. IDs das propostas são determinísticos por checkpoint e posição na resposta, preservados na passagem parcial→completa. `analysis_hash` permanece nulo até a conclusão.

## Seleção editorial e execução

`GET/PUT /api/v1/projects/{id}/analysis-selection` lê/salva `{schema_version, analysis_hash, candidate_ids}`. `PUT` rejeita hashes antigos, IDs desconhecidos/duplicados e propostas inelegíveis. Uma lista vazia permite limpar a escolha.

`POST /api/v1/projects/{id}/jobs` com operação `render` recebe `options.analysis_hash` e `options.candidate_ids`. O worker recebe uma cópia desses valores. Uma lista explícita não aplica o limite automático de três ou remove variantes sobrepostas. Integridade e duração seguem obrigatórias. Clientes antigos que omitem seleção conservam o comportamento automático.

Retomada usa somente IDs ainda pendentes/falhos do snapshot do trabalho. Esse subconjunto não substitui a seleção editorial persistida. Renderização não usa o Gemini e valida novamente a identidade da análise.

## Progresso de geração

`Job.progress` preserva `stage/steps` e agrega `schema_version`, `operation`, `phase`, `current_candidate_id`, `current_index`, `total_items`, `completed_items`, `failed_items`, `processed_us`, `total_us`, `activity_at` e `items`.

Cada item possui identidade/título, estado (`pending`, `running`, `ready`, `failed`), fase, tempos, e opcionalmente `revision_id`, `error_code` e `reused`. Fases: edição, pausas, legendas, codificação, verificação e pronto. `out_time_us` é limitado à duração do EDL e monotônico. Codificação em 100% não significa pronto; somente a verificação técnica publica a prévia. Sem total mensurável, a UI exibe atividade/tempo decorrido e não calcula percentual ou ETA.

Leitores de stdout e stderr drenam os pipes simultaneamente. Cancelamento interrompe o processo pertencente ao worker. Telemetria pública não contém stderr ou respostas brutas do provedor.

## Revisões e exportação

O worker é o único escritor do índice `project.json` durante a geração; cada prévia verificada é publicada imediatamente. Decisões escrevem somente `review.json`, evitando sobrescrever cortes recém-publicados. A leitura de revisões calcula o estado da aprovação pela decisão e fingerprint.

Uma receita alterada de legendas/formato/render cria outra revisão; arquivos e decisões anteriores permanecem disponíveis. O padrão `CropArtifact.mode` agora é `center-crop` (9:16 central estático). `fit-blur` continua aceito na leitura de contratos antigos; novas renderizações produzem recorte central, sem blur ou sobreposição.

Exportação continua exigindo aprovação humana válida e checksums. Nada nesta interface transforma QA técnica ou flags do Gemini em aprovação editorial automática.

A escrita atômica repete brevemente conflitos Windows de compartilhamento (WinError 5/32), com limite de tentativas. Isso evita que a consulta de progresso interrompa a codificação. Falhas permanentes continuam visíveis; arquivos parciais nunca são publicados. FFmpeg usa dois threads na decodificação/codificação e nos filtros para conter a competição de CPU em notebooks.
