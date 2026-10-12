# Modelo de dados e contratos do pipeline v1

Especificação para implementação futura. Não usar dictionaries upstream como API pública. JSON UTF-8; `schema_version` em todas as fronteiras; sem `NaN`, floats infinitos ou unidades implícitas.

## Convenções

- IDs UUID, únicos por entidade. `word_id` estável dentro de uma revisão de transcrição; modelo novo cria transcript_id e novos word IDs.
- Tempo inteiro `*_us`, intervalo semiaberto `[start_us,end_us)`, 0 ≤ start < end. Duração da mídia e intervalos limitam todos os tempos.
- Índices de palavras no adapter são base 0 e inclusivos apenas se o upstream assim exigir; domínio usa IDs e intervalo temporal semiaberto. Não assumir que um comentário de código define corretamente a convenção upstream.
- FPS/timebase como `{num,den}` com den>0. PTS original, normalização e deslocamento preservados. Source hash SHA-256 de bytes; parâmetros/prompt em JSON canônico UTF-8 ordenado, sem incluir segredos.
- Timestamps administrativos RFC3339 UTC. Paths de artefatos relativos à raiz do projeto; proibir traversal e paths de output fora da raiz/export escolhido.
- Revisions imutáveis. Revisão aprovada refere source hash, transcript revision, EDL revision e caption revision; mudar um deles exige reaprovar.

## Entidades SQLite

| Entidade | Campos principais | Relações/regras |
|---|---|---|
| Project | id, name, root_path, created_at, updated_at, schema_version | Root único; não apagar sources por cascade |
| Source | id, project_id, sha256, kind, local_path, original_url, original_title, channel, attribution, rights_note, duration_us, probe_artifact_id | Unique(project_id,sha256); manter prova de origem, não deduzir autorização pelo URL |
| ModelInstallation | id, provider, model_name, revision_digest, path, size_bytes, license_id, offline_ready | Instalação global; referência por execução; digest obrigatório para congelar benchmark |
| Job | id, project_id, source_id, status, config_json, config_hash, created_at, heartbeat_at, lease_owner, error_code | Estados definidos no PRD; config sem segredo |
| StageRun | id, job_id, stage, stage_version, attempt, cache_key, status, started_at, ended_at, error_json | Unique(job_id,stage,attempt); uma tentativa ativa por stage; índice de cache |
| Artifact | id, source_id, kind, schema_version, relative_path, sha256, size_bytes, manifest_json | Artefato pronto tem hash/size validado; não sobrescrever conteúdo |
| StageInput / StageOutput | stage_run_id, artifact_id | Relações N:N para DAG/invalidação e provenance |
| TranscriptRevision | id, source_id, artifact_id, model_id, language, parent_id | ASR bruto imutável; words no JSON; corrections em revisão separada |
| Clip | id, project_id, source_id, proposal_artifact_id, review_status | Identidade do corte, independente de export |
| ClipRevision | id, clip_id, parent_id, transcript_id, edl_artifact_id, crop_artifact_id, caption_artifact_id, metadata_artifact_id, author_kind, reason, created_at | Revisão imutável; documento cobre tudo usado no render |
| ReviewDecision | id, clip_revision_id, decision, notes, checks_json, created_at | Aprovação/rejeição por revisão; decisão anterior permanece |
| ExportBatch / ExportItem | ids, revision_id, profile_hash, status, output_artifact_id, validation_artifact_id | Item concluído só depois de QA; erro individual isolado |
| JobEvent | job_id, seq, kind, stage, payload_json, created_at | PK(job_id,seq); eventos retomáveis por seq |

Foreign keys ativadas, WAL, busy_timeout de 5 s, migrations com backup. Não guardar tokens, cookies ou API keys no SQLite. Fazer limpeza pela referência dos artefatos; deletar cache órfão em ação explícita, sem afetar revisões/exportações aprovadas.

## Contratos e interfaces

`StageRequest`: schema_version=`1.0`, job_id, stage, stage_version, inputs (id,kind,sha256,path), config, runtime (device,thread_budget,offline), cancellation_token_id.

`StageResult`: schema_version, status=`completed|failed|cancelled`, artifacts (id,kind,path,sha256,size_bytes), warnings, metrics (wall_ms, peak_rss_bytes nullable), error nullable. Status failed tem error; completed não tem error e artifacts validados. Sem texto livre substituindo campos obrigatórios.

Interfaces futuras do motor: `Transcriber.transcribe(AudioArtifact, ASRConfig) -> TranscriptArtifact`; `Analyzer.analyze(TranscriptArtifact, AnalysisConfig) -> AnalysisArtifact`; `Selector.select(AnalysisArtifact, TranscriptArtifact, SelectionConfig) -> CandidateArtifact`; `EditPlanner.plan(Candidate, Transcript, SilenceMap, EditConfig) -> EDLArtifact`; `Tracker.track(Source, EDL, TrackingConfig) -> CropArtifact`; `CaptionBuilder.build(Transcript, EDL, CaptionRevision) -> CaptionArtifact`; `Renderer.render(Source, EDL, Crop, Captions, ExportConfig) -> RenderArtifact`. Orchestrator decide ordem/retomada; adapters não escrevem no banco.

### Transcript v1

```json
{
  "schema_version": "1.0",
  "transcript_id": "00000000-0000-4000-8000-000000000001",
  "source_id": "00000000-0000-4000-8000-000000000002",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "language": "pt",
  "model": {"provider": "faster-whisper", "name": "small", "digest": "sha256:example"},
  "words": [
    {"id": "w0001", "text": "Não", "start_us": 1000000, "end_us": 1250000, "probability": 0.94, "speaker_id": null},
    {"id": "w0002", "text": "concordo.", "start_us": 1300000, "end_us": 1900000, "probability": 0.91, "speaker_id": null}
  ],
  "segments": [{"id": "s0001", "word_ids": ["w0001", "w0002"], "text": "Não concordo.", "start_us": 1000000, "end_us": 1900000}],
  "warnings": []
}
```

Exemplo sintético, não transcrição do vídeo. Model digest de produção deve ser real, não o valor didático. Probabilidade ASR não é probabilidade de verdade; pode ser null se backend não fornecer. Palavras temporalmente sobrepostas em fala simultânea recebem warning, não têm seus tempos silenciosamente corrigidos para fingir ordem perfeita.

### Analysis/Candidate v1

Temas: id, label, summary, evidence_word_ids, dependências de contexto e possíveis ressalvas. Candidates: id, topic_id, start_word_id, end_word_id, evidence_word_ids, rationale, context_before_word_ids, context_after_word_ids, editorial (completeness, standalone_context, qualification_preserved, all com valores `yes|no|uncertain`), title_suggestion, description_suggestion, warnings.

O LLM responde JSON estrito; references existentes e end≥start são validadas deterministicamente. `uncertain` exige revisão, `no` rejeita automação. Timestamps são resolvidos pelo motor com fonte e transcript_id, não emitidos pelo LLM. Uma resposta vazia válida é diferente de erro de transporte/schema. Não usar campo de score viral.

### EDL v1

```json
{
  "schema_version": "1.0",
  "revision_id": "00000000-0000-4000-8000-000000000003",
  "source_id": "00000000-0000-4000-8000-000000000002",
  "transcript_id": "00000000-0000-4000-8000-000000000001",
  "policy": "continuous_selection_with_verified_pause_removal",
  "spans": [
    {"source_start_us": 1000000, "source_end_us": 3000000, "output_start_us": 0, "output_end_us": 2000000, "speed_num": 1, "speed_den": 1},
    {"source_start_us": 4200000, "source_end_us": 5200000, "output_start_us": 2000000, "output_end_us": 3000000, "speed_num": 1, "speed_den": 1}
  ],
  "removed": [{"start_us": 3000000, "end_us": 4200000, "reason": "verified_pause", "evidence_artifact_ids": ["silence-map-id", "vad-map-id"]}],
  "protected_word_ids": ["w0001", "w0002"],
  "duration_us": 3000000,
  "warnings": []
}
```

Validar spans monotônicos, source bounds, speed=1 na PoC e nenhuma lacuna/sobreposição na saída. Dentro de um span `source_time = source_start + (output_time-output_start)*speed_num/speed_den`. Na junção semiaberta, o instante pertence ao próximo span. O inverso retorna null para tempo removido e span ID para origem presente. Soma das durações = duration_us, até um microssegundo de arredondamento por span. Testar além disso o erro após quantização em frames/samples.

Removed spans não podem tocar palavras protegidas + margem. Toda palavra pertencente ao corte tem cobertura completa em span mantido ou invalida o plano; QA lexical por transcrição de saída é auxiliar, não a fonte da preservação.

### Crop/Caption/Export v1

Crop: source_id, edl_revision_id, target_size, scenes com ranges source/output, keyframes `{source_us,x,y,width,height}`, face_track_id, confidence e fallback_reason. Coordenadas no vídeo orientado normalizado; interpolação limitada à própria cena/span EDL. Render valida dimensão, bounds e coordenadas pares.

Caption: transcript_id, edl_revision_id, revision_id, style_id, words `{source_word_id,display_text,output_start_us,output_end_us,edited_by}`, cues, font/license ref. Sem mudança implícita do texto fonte; flags para palavra com timing ausente.

Export: revision_id, profile (codec, size, fps racional, audio), files com SHA-256/bytes, duration_us, source attribution, model/prompt/code provenance, warnings, QA report e review decision ID. JSON referencia artefatos; MP4/ASS/SRT/word JSON são outputs irmãos. Não emitir “aprovado” se revisão humana ainda não existe.

### Erros e versionamento

Erro: code, stage, message, retryable, details sem segredos. Códigos iniciais: SOURCE_UNAVAILABLE, SOURCE_CHANGED, NO_SPEECH, MODEL_MISSING, MODEL_INCOMPATIBLE, PROVIDER_UNAVAILABLE, PROVIDER_INVALID_OUTPUT, INCOMPLETE_ARGUMENT, UNSAFE_EDIT, TRACKING_UNCERTAIN, DISK_FULL, RENDER_FAILED, CANCELLED, UNSUPPORTED_SCHEMA.

Major incompatível rejeitada antes de executar; minor adiciona campos opcionais com default documentado. Validar JSON Schema na fronteira e invariantes temporais no domínio. Persistir schemas junto aos artefatos; migração gera nova revisão, nunca altera artefato já aprovado.
