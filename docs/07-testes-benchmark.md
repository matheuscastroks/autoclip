# Plano de testes e avaliação com vídeo real

## Entrada comum

[Vídeo escolhido pelo usuário](https://www.youtube.com/watch?v=z0cf-eWBVCo): Jones Manoel, “É preciso dialogar com a frustração e raiva das pessoas”. Download local confirmado, 184.894.331 bytes, duração ffprobe 1773,194 s. SHA-256 `bc190e8b2d93ab3c3d9d413402d3c11da1a060ea45b2e3ac961f5417cf19c396`. Metadados da página tinham duração aproximada divergente; usar o arquivo decodificado como referência de tempo.

Amostra de smoke ASR: 60–180 s da mesma fonte, WAV mono PCM16 a 16 kHz; hash `595a283ec3c4fdfc65a1c5dd2be247ba3b7029764b725e38125c4dc513e54237`. Não escolher esse pedaço por favorecimento de resultados. A amostra prova execução técnica apenas; não é comparação semântica do vídeo integral.

## Duas trilhas de comparação

**Nativa:** versões/SHA, defaults e alterações mínimas de CPU/português para cada candidato. Registrar se requer conta, modelo externo, shell POSIX, GPU ou módulo não permissivo. Erro e não aplicável não recebem zero disfarçado de nota de qualidade.

**Controlada:** mesma source hash; ASR small multilíngue CPU/int8 quando disponível; mesmo LLM/digest local e limite 60 s se o candidato aceitar configuração sem reescrita. jameselle com Claude Code não é equivalente a um seletor local; testar EDL manual somente como render/QA, sem contar isso como seleção automática. auto-editor participa da remoção/EDL, sem competir como seletor semântico.

**Atualização de configuração:** usuário escolheu Gemini API nesta máquina. A rodada semântica passa a usar o mesmo modelo Gemini e parâmetros nos candidatos que o suportam; adapters necessários são registrados como adaptações. Não comparar Claude/local versus Gemini como se fossem o mesmo modelo. Modelo remoto pode mudar: guardar nome/version retornada, data e payload hash. Ensaios offline se aplicam a ASR/render/revisão; seleção Gemini testa falha de conexão, quota e payload somente textual.

Processos pesados em série. Um ensaio frio e três aquecidos após provisionamento, wall time por etapa, RSS pico por processo/árvore, modelo de CPU/RAM, tamanho dos modelos e disco. Reportar mediana e faixa; evitar extrapolar 120 s para 30 minutos sem ensaio integral. Benchmarks desta primeira rodada, quando únicos, são smoke e não ranking de velocidade.

## Rubrica editorial

Revisar até três cortes por candidato, com ordem aleatória e labels ocultos. Ouvir fonte pelo menos 30 s antes e depois; ampliar contexto até resolver anáfora/ressalva. Dois revisores independentes quando disponíveis; um só implica limitação registrada. Concordância e divergências entram no relatório.

| Dimensão | Escala e critério |
|---|---|
| Completude | 0: fragmento; 1: conclusão ou premissa faltante; 2: entendimento parcial; 3: pensamento completo |
| Contexto autônomo | 0: incompreensível; 1: referência forte ausente; 2: pequena dependência; 3: autônomo |
| Densidade informativa | 0: vazio; 1: repetitivo; 2: alguma informação; 3: informação clara e útil |
| Integridade | Falha crítica sim/não; negar ou inverter sentido, omitir ressalva necessária, alterar número/autoria ou fabricar relação |
| Bordas e pausas | Palavra cortada sim/não; respiração/pontuação natural sim/não; edição audível anotada |
| Reframe e captions | Rosto inteiro/estabilidade/legibilidade; offset medido em palavras anotadas |

Gate por corte: zero falhas críticas, completude=3, contexto≥2, nenhuma palavra cortada. Não compensar integridade baixa com boa estética. Aceitar zero cortes se nenhum intervalo satisfizer o requisito. Registrar razão de rejeição e comparar mudanças de prompt/modelo contra a mesma anotação.

## ASR português

Anotar manualmente trechos distribuídos no começo/meio/fim e fala rápida, pelo menos 5 minutos totais no vídeo integral. WER normalizado (caixa/pontuação) e CER com acentos separados; retenção de negações, nomes, datas e números medida à parte. Hipóteses não corrigidas não servem como ground truth. Legenda automática do YouTube não é referência humana.

Meta inicial proposta: WER ≤15% no corpus limpo e nenhuma falha crítica não sinalizada em conteúdo aprovado; adaptar modelo quando não atingir. Timing: p95 de erro absoluto início/fim por palavra ≤200 ms no conjunto anotado; testar bordas com zoom de áudio. Timestamps por palavra do Whisper são estimativas, não alinhamento forçado garantido.

## Testes automatizados

| Nível | Casos | Aceite |
|---|---|---|
| Contratos | campos ausentes, major inválida, IDs/NaN/out-of-range | rejeitar antes de persistir/editar |
| Propriedades EDL | spans aleatórios, joins, origem removida, frações | round-trip dentro do span; saída sem lacunas; proteção de toda palavra |
| Seleção | negação, condicional, ressalva tardia, anáfora, quote e JSON malformado | validação estrutural; flags de revisão; nunca excluir ressalva pelo score |
| Pausas | fala baixa, música, respiração, palavra ASR ausente, silêncios longos | só remover interseção comprovada; caso incerto preserva |
| Retomada/cache | checksum errado, config/model/prompt alterados, processo morto | recomputar só dependentes; não reutilizar arquivo parcial |
| Render | VFR, rotation, offset de áudio, sem áudio, paths UTF-8/espaço/apóstrofo | sync, decodificação, codec/size/fps corretos; nenhuma perda por quoting |
| Tracking | oclusão, rosto na borda, troca de cena, dois rostos | fallback/reset; sem transição através de cut |
| Localidade | rede externa bloqueada, Ollama desligado, modelo ausente | erro útil sem nuvem; processamento completo após provisionamento |
| API/projetos | token errado, traversal, conflito de revisão, batch parcial | isolamento, idempotência, nenhum output fora da raiz |
| Resiliência | cancel/disco cheio/limite RAM/kill/relink | fonte preservada; artefato parcial não concluído |

Testes de provider usam stub para schema/erros, mas aceitação semântica exige LLM real + revisão humana. Testes upstream com mocks não provam qualidade do detector/ASR. Ao expor API, usar Postman CLI instalado para collection v1 e asserts de status/schema/retomada; nenhum endpoint foi criado nesta etapa.

## Corpus após vídeo comum

Adicionar conteúdo autorizado: monólogo limpo; entrevista duas pessoas; fala rápida com números/negações; ruído/música e baixa voz; rosto móvel/oclusão; slides com narrador; vídeo VFR/rotacionado de celular. Pelo menos 3 fontes por categoria crítica para não ajustar tudo a um único vídeo. Guardar consentimento/licença e não versionar mídia sensível/publicamente redistribuída.

## Saída da avaliação

CSV/JSON por execução: candidate, repo_sha, source_sha256, config/model/prompt hashes, stage status, wall_ms, peak_rss_bytes, clips/proposal IDs, review ratings, critical failures, notes e artifacts. Células pendentes ficam null com reason; não usar score viral. Matriz de decisão só ganha dimensão de qualidade depois dessa etapa.
