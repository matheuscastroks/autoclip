# Roadmap com gates e critérios de aceite

Este é o backlog proposto solicitado no briefing, não autorização para a implementação completa. Base escolhida: OpenShorts. Sem estimativa de prazo antes de medir o motor e a máquina CPU.

## M0 — investigação, corpus e arquitetura

- [x] Identificar cinco candidatos por SHA; ler licenças, dependências e pontos críticos.
- [x] Registrar OpenShorts como base escolhida pelo usuário.
- [x] Importar vídeo comum, verificar ffprobe e checksum, extrair amostra fixa.
- [ ] Concluir comparativo editorial dos cinco candidatos, registrando impedimentos de execução.
- [ ] Revisar PRD, arquitetura e contratos escritos com o usuário.

Aceite: nenhuma nota de qualidade inventada; arquivo fonte único para todos; resultados reproduzíveis; diferenças de modelo/config anotadas. Aprovação do desenho desbloqueia o plano detalhado da PoC.

## M1 — PoC do motor OpenShorts, sem desktop

1. Congelar snapshot upstream e lista de arquivos MIT selecionados. Criar attribution/UPSTREAM e teste que instala/roda sem `cloud/`. Não copiar módulo comercial como atalho.
2. Extrair adapters ASR/seleção/EDL/render; config explícita por job em vez de env global. CLI invoca fluxo sem importar `app.py` ou dashboard.
3. Rodar vídeo integral, Whisper small multilíngue em CPU, transcrição por palavra. Guardar artefatos v1 e metadados do modelo.
4. Configurar Gemini API escolhido pelo usuário, credencial no keyring e modelo explícito; prompt em PT-BR exigindo pensamento completo e ressalvas. Enviar somente texto; gerar até três cortes de 20–60 s ou zero candidatos explicado. Registrar modelo/versão retornada, payload hash e uso; sem troca automática de provider.
5. Seleção contínua, sem redução de pausas neste primeiro ensaio. Exportar MP4 vertical conservador, ASS/SRT, word JSON, EDL e metadados de fonte. Tracking só entra se aprovado; inicialmente fit-blur é fallback explicitamente rotulado.
6. Verificar arquivo final, ouvir início/fim e revisar contexto completo. Reiniciar job após interromper ASR/render e confirmar retomada de artefatos válidos.

Arquivos previstos: `engine/contracts/`, `engine/adapters/openshorts/`, `engine/pipeline/`, `engine/cli.py`, `tests/unit/`, `tests/integration/`; vendor permissivo separado. As assinaturas públicas estão no documento de contratos; detalhes de implementação pertencem ao plano após revisão.

Aceite: ASR/edição/render funcionam sem rede externa após provisionamento; seleção Gemini usa internet e só envia texto; nenhuma palavra ou ressalva truncada nos cortes aprovados; fonte preservada; export validado por ffprobe; revisão ligada ao hash da fonte; retomada não usa cache alterado. PoC não é concluída apenas porque o MP4 foi criado.

## M2 — pausas e reenquadramento

- Implementar SilenceMap/VADMap e EditPlanner que respeita regiões protegidas; permitir ligar/desligar e comparar A/B.
- Integrar detector/licença escolhidos, scene reset e crop path com fallback.
- Validar efeitos da EDL em legenda, áudio e tracking; preview menor e export 1080×1920.

Aceite: nenhum overlap com regiões protegidas, ≥95% dos frames amostrados com rosto principal inteiro quando o rosto é visível; sem interpolação através de corte; ausência de face/ambiguidade recebe fallback, não movimento aleatório. Pausas são naturais na escuta; metas são critérios propostos, não resultados obtidos.

## M3 — projetos e API local

- SQLite, revisions, eventos, leases, fila e manifests; migrations com backup.
- API v1 consumindo o mesmo domínio da CLI; token loopback e paths confinados.
- Jobs canceláveis e retomáveis; batches isolados por projeto/revisão.

Aceite: reiniciar não perde projeto/decisões; relink exige checksum; dois projetos não colidem; falha/disco cheio não publica artefato parcial; API testa sem GPU/LLM real, integração adicional usa modelos reais.

## M4 — revisão desktop

- Vue/Tauri: importação, fila, transcript, candidatos, comparação com contexto original, bordas, pausas, crop, correções de captions, fonte e export.
- Tauri inicia/encerra sidecar; mostra estado do modelo e modo local/remoto.
- Reutilizar conceitos de revisão do OpenShorts; não portar billing/UGC/publicação ou assumir que JSX vira Vue diretamente.

Aceite: usuário revê/aprova/exporta um projeto e reabre a mesma revisão; atalhos e controles acessíveis; edição não executa inferência longa na thread da UI; rede externa nunca é ativada silenciosamente.

## M5 — distribuição open source

- Escolher licença do produto compatível com código/dependências; emitir SBOM por release.
- Empacotar sidecar/runtime/model provisioning, fontes e FFmpeg com documentação correspondente.
- Testar instalação Windows limpa, CPU, paths especiais e operação offline; documentar requisitos medidos.

Aceite: pacote sem `cloud/`; cada binário/peso possui licença e origem; desinstalação não apaga projetos; restore/export seguem contratos; suite/corpus sem falhas críticas. Depois desse gate, estudar entrevistas multipessoa e outras otimizações.
