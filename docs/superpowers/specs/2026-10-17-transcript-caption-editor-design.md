# Especificação de Design: Editor de Legendas na Tela de Transcrição

**Data**: 2026-10-17  
**Status**: Proposto  
**Escopo**: `engine/api`, `desktop/src/components/TranscriptPanel.vue`, `desktop/src/api`

---

## 1. Contexto e Objetivos

Atualmente, a tela de **Transcrição** (`TranscriptPanel.vue`) do AutoClip é estritamente somente-leitura, servindo para consulta do texto reconhecido pelo motor ASR (Faster-Whisper) sincronizado com o player de vídeo original.

No entanto, modelos ASR frequentemente cometem erros pontuais de ortografia, nomes próprios, termos técnicos ou pontuação. Quando os cortes de vídeo são gerados e têm as legendas queimadas (`.ass`/`.srt`), esses erros acabam aparecendo no vídeo final.

### Objetivo
Transformar a tela de transcrição em um **editor interativo de legendas**, permitindo ao usuário:
1. Identificar trechos com erros enquanto assiste ao vídeo original com sincronia de áudio.
2. Editar e corrigir palavras e frases diretamente na lista de segmentos, com botão de edição ágil.
3. Salvar as correções garantindo que **a sincronização de timestamps de áudio nunca seja perdida** e que as estruturas do pipeline (análise por IA, EDL e geração de legendas) continuem íntegras.
4. Refletir automaticamente o texto corrigido na geração das legendas de cortes futuros e permitir atualização das legendas existentes.

---

## 2. Estratégia de Sincronização e Não-Regressão

### 2.1 Preservação dos Limites de Tempo (Intervalos)
- Cada palavra transcrita possui um intervalo de microssegundos `[start_us, end_us]`.
- Cada segmento agrupa uma sequência de palavras cobrindo o intervalo do início da primeira palavra ao fim da última palavra.
- **Regra**: O áudio do locutor ocorreu em um tempo real imutável. Portanto:
  - Se o usuário apenas corrige o texto de palavras existentes (1:1), os tempos de cada palavra são 100% mantidos.
  - Se o usuário insere palavras extras ou remove palavras de um segmento:
    - O intervalo total do segmento `[seg.start_us, seg.end_us]` é preservado.
    - O tempo total é distribuído proporcionalmente entre as palavras do novo texto.
    - A lista de palavras mantém a ordenação estrita `start_us < end_us` exigida pelo validador `TranscriptArtifact.valid_words`.

### 2.2 Compatibilidade com AI Analysis e EDL
- O `AnalysisArtifact` e o `EDLArtifact` usam os IDs das palavras (`covered_word_ids`, `start_word_id`, `end_word_id`).
- Ao atualizar o texto das palavras existentes no `transcript.json`, os identificadores originais das palavras e suas ordens temporais são preservados.
- O hash do conteúdo da transcrição é mantido válido para reprodução e renderização.

---

## 3. Arquitetura da Solução

### 3.1 Backend: Novo Endpoint na API do Motor (`engine/api/app.py`)
- **Rota**: `PUT /api/v1/projects/{pid}/transcript`
- **Validação de Bloqueio**: Utiliza `editable(pid)` para impedir alterações concorrentes se uma tarefa de transcrição ou renderização estiver em andamento.
- **Contrato de Entrada (`UpdateTranscriptInput`)**:
  ```python
  class SegmentUpdate(Contract):
      id: str
      text: str

  class UpdateTranscriptInput(Contract):
      segments: list[SegmentUpdate]
  ```
- **Processamento**:
  1. Carrega o `transcript.json` existente do projeto.
  2. Para cada segmento atualizado:
     - Localiza o segmento pelo `id`.
     - Atualiza o `text` do segmento.
     - Atualiza o `text` das palavras (`Word`) vinculadas ao segmento, recalculando a distribuição temporal de forma suave caso haja alteração na contagem de palavras.
  3. Valida o novo modelo via `TranscriptArtifact`.
  4. Grava atomicamente (`atomic_json`) no diretório do projeto.
  5. Atualiza o `word_count` do projeto.
  6. Retorna o `TranscriptArtifact` atualizado.

### 3.2 Frontend: API Client (`desktop/src/api/projects.ts` e `desktop/src/api.ts`)
- Adicionar o método:
  ```typescript
  updateTranscript: (id: string, payload: { segments: { id: string; text: string }[] }) =>
    request<Transcript>(`/projects/${id}/transcript`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  ```

### 3.3 Frontend: Interface do Usuário (`desktop/src/components/TranscriptPanel.vue`)
- **Modo de Edição Inline por Segmento**:
  - Cada segmento possui um estado normal e um estado editável.
  - No estado normal:
    - Exibe o timestamp `<time>` e o texto `<p>`.
    - Ao passar o mouse (ou ao focar via teclado), exibe um botão de ação com ícone `pencil` ou `edit` ("Editar trecho").
  - No estado de edição:
    - O parágrafo é substituído por um `<textarea>` estilizado com foco visual claro.
    - Controles de ação:
      - Botão "Salvar" (`Enter` ou clique).
      - Botão "Cancelar" (`Esc` ou clique).
    - Teclas de atalho: `Enter` salva, `Shift+Enter` quebra linha, `Esc` cancela.
  - **Player de Vídeo Sincronizado**:
    - Permite que o usuário dê play/pause no trecho enquanto digita a correção para conferir a fala.
  - **Feedback**:
    - Indicador de salvamento em andamento.
    - Notificação toast de sucesso.
    - A busca (`query`) e a contagem de palavras reagem instantaneamente.

---

## 4. Plano de Testes e Verificação

### 4.1 Testes de Backend (Python / pytest)
- `tests/unit/test_transcript_update.py`:
  - Testar atualização de texto de palavra mantendo timestamps idênticos.
  - Testar adição e remoção de palavras em um segmento com redistribuição proporcional do tempo.
  - Testar rejeição de IDs inválidos e preservação do `transcript_id`.
  - Testar renderização de legenda (`OpenShortsCaptionBuilder`) utilizando a transcrição editada.

### 4.2 Testes de Frontend (TypeScript / Vitest)
- `desktop/tests/transcript-editing.test.ts`:
  - Testar transição para modo de edição ao acionar o botão de editar.
  - Testar envio correto da requisição `PUT /api/v1/projects/{pid}/transcript`.
  - Testar cancelamento via tecla `Esc` restaurando o texto original.
  - Testar atualização reativa do segmento na tela após o retorno da API.
- Executar a suíte completa com `npm --prefix desktop run test:run` e `pytest -m "not real_media" -q`.
