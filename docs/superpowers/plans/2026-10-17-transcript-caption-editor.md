# Implementação do Editor de Legendas na Tela de Transcrição

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir edição e correção de frases e palavras diretamente na tela de transcrição do AutoClip, preservando os timestamps originais de áudio para sincronia perfeita e alimentando as legendas dos cortes gerados.

**Architecture:** Adição do endpoint `PUT /api/v1/projects/{pid}/transcript` no motor Python para atualizar o `transcript.json` com redistribuição proporcional do tempo sem alterar os limites do segmento; integração com o cliente de API no frontend e evolução do `TranscriptPanel.vue` para oferecer edição inline por segmento com validação, atalhos de teclado e player de sincronia.

**Tech Stack:** Python 3.12 (FastAPI, Pydantic, pytest), TypeScript, Vue 3, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-17-transcript-caption-editor-design.md`

## Global Constraints
- Python 3.12, tipagem rigorosa Pydantic `Contract` com `extra='forbid'`, `validate_assignment=True`.
- Preservar invariantes: `TranscriptArtifact.valid_words` (`start_us < end_us`, ordenação estrita, IDs únicos).
- Manter acessibilidade e regras de UI: atalhos `Enter` (salvar) e `Esc` (cancelar), layout responsivo sem quebras visuais.
- Nenhuma dependência externa adicional permitida.

## Review Focus
1. Atualização com mais palavras do que o original não pode produzir timestamps sobrepostos ou decrescentes.
2. Atualização com menos palavras não pode gerar duração nula ou menor que 1 microssegundo.
3. Edição quando uma tarefa (`job`) estiver ativa no projeto deve retornar status HTTP 409 impedindo corrupção de estado.
4. Tentativa de editar segmento inexistente no projeto deve retornar erro 422/404 explícito.
5. Cancelar a edição na UI (via `Esc` ou botão) deve restaurar imediatamente o texto anterior sem disparar chamadas de API.

---

### Task 1: Engine - Modelos de Contrato de Atualização de Transcrição

**Files:**
- Modify: `engine/contracts/api.py`
- Test: `tests/unit/test_transcript_update_contracts.py`

**Interfaces:**
- Produces: `SegmentUpdate`, `UpdateTranscriptInput` em `engine.contracts.api`.

- [ ] **Step 1: Escrever teste de contrato que falha**

```python
# tests/unit/test_transcript_update_contracts.py
import pytest
from pydantic import ValidationError
from engine.contracts.api import SegmentUpdate, UpdateTranscriptInput

def test_segment_update_valid():
    up = SegmentUpdate(id='s1', text='Texto corrigido')
    assert up.id == 's1'
    assert up.text == 'Texto corrigido'

def test_segment_update_invalid():
    with pytest.raises(ValidationError):
        SegmentUpdate(id='', text='Texto')
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `pytest tests/unit/test_transcript_update_contracts.py -v`
Expected: FAIL com ImportError ou ValidationError.

- [ ] **Step 3: Implementar `SegmentUpdate` e `UpdateTranscriptInput` em `engine/contracts/api.py`**

Adicionar classes herdando de `Response` com campos validados (`id: str = Field(min_length=1)`, `text: str = Field(min_length=1)`).

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `pytest tests/unit/test_transcript_update_contracts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_transcript_update_contracts.py engine/contracts/api.py
git commit -m "feat(engine): define transcript update request contracts"
```

---

### Task 2: Engine - Algoritmo de Atualização com Preservação de Sincronia de Timestamps

**Files:**
- Create: `engine/editorial/transcript_editor.py`
- Test: `tests/unit/test_transcript_editor.py`

**Interfaces:**
- Consumes: `TranscriptArtifact` de `engine.contracts`, `SegmentUpdate` de `engine.contracts.api`.
- Produces: `apply_transcript_updates(transcript: TranscriptArtifact, updates: list[SegmentUpdate]) -> TranscriptArtifact`

- [ ] **Step 1: Escrever testes unitários para preservação de sincronia**

```python
# tests/unit/test_transcript_editor.py
from engine.contracts import TranscriptArtifact, Word, Segment
from engine.contracts.api import SegmentUpdate
from engine.editorial.transcript_editor import apply_transcript_updates

def make_sample_transcript():
    words = [
        Word(id='w0', text='Olá', start_us=0, end_us=500_000),
        Word(id='w1', text='mundo', start_us=500_000, end_us=1_000_000),
    ]
    segments = [
        Segment(id='s0', text='Olá mundo', start_us=0, end_us=1_000_000, word_ids=['w0', 'w1'])
    ]
    return TranscriptArtifact(
        source_id='00000000-0000-0000-0000-000000000001',
        source_sha256='a' * 64,
        words=words,
        segments=segments,
    )

def test_edit_word_preserves_exact_timestamps():
    t = make_sample_transcript()
    updated = apply_transcript_updates(t, [SegmentUpdate(id='s0', text='Oi mundo')])
    assert updated.words[0].text == 'Oi'
    assert updated.words[0].start_us == 0
    assert updated.words[0].end_us == 500_000
    assert updated.words[1].text == 'mundo'

def test_edit_segment_with_different_word_count_preserves_boundaries():
    t = make_sample_transcript()
    updated = apply_transcript_updates(t, [SegmentUpdate(id='s0', text='Olá meu caro amigo')])
    assert updated.segments[0].start_us == 0
    assert updated.segments[0].end_us == 1_000_000
    assert updated.words[0].start_us == 0
    assert updated.words[-1].end_us == 1_000_000
    assert all(b.start_us >= a.end_us for a, b in zip(updated.words, updated.words[1:]))
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `pytest tests/unit/test_transcript_editor.py -v`
Expected: FAIL com "module not found".

- [ ] **Step 3: Implementar `apply_transcript_updates` em `engine/editorial/transcript_editor.py`**

Distribuir proporcionalmente os tempos para novas palavras preservando `seg.start_us` e `seg.end_us` e garantindo `start_us < end_us`.

- [ ] **Step 4: Executar testes para verificar aprovação**

Run: `pytest tests/unit/test_transcript_editor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/editorial/transcript_editor.py tests/unit/test_transcript_editor.py
git commit -m "feat(engine): implement transcript timing preservation editor"
```

---

### Task 3: Engine - Rota de API `PUT /api/v1/projects/{pid}/transcript`

**Files:**
- Modify: `engine/api/app.py`
- Test: `tests/integration/test_transcript_api.py`

**Interfaces:**
- Consumes: `apply_transcript_updates`, `UpdateTranscriptInput`, `store`, `jobs`.
- Produces: Endpoint HTTP `PUT /api/v1/projects/{pid}/transcript`.

- [ ] **Step 1: Escrever teste de integração de API**

```python
# tests/integration/test_transcript_api.py
def test_put_transcript_updates_file_and_word_count(client, project_with_transcript):
    pid = project_with_transcript['id']
    resp = client.put(f'/api/v1/projects/{pid}/transcript', json={
        'segments': [{'id': 's0', 'text': 'Novo texto da legenda'}]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert 'Novo texto da legenda' in [s['text'] for s in data['segments']]
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `pytest tests/integration/test_transcript_api.py -v`
Expected: FAIL 405 Method Not Allowed ou 404.

- [ ] **Step 3: Implementar rota `update_transcript` em `engine/api/app.py`**

Adicionar handler `@app.put('/api/v1/projects/{pid}/transcript')` com lock, `editable(pid)`, chamada a `apply_transcript_updates`, gravação atômica em `transcript.json` e retorno do transcript serializado.

- [ ] **Step 4: Executar teste para verificar aprovação**

Run: `pytest tests/integration/test_transcript_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/api/app.py tests/integration/test_transcript_api.py
git commit -m "feat(api): add PUT endpoint for project transcript updates"
```

---

### Task 4: Desktop - Integração da API no Frontend

**Files:**
- Modify: `desktop/src/api/projects.ts`
- Modify: `desktop/src/api.ts`
- Test: `desktop/tests/projects-api.test.ts` (ou teste unitário do cliente)

**Interfaces:**
- Produces: `api.updateTranscript(id: string, payload: { segments: { id: string; text: string }[] })`

- [ ] **Step 1: Escrever teste de chamada da API**

Verificar se `updateTranscript` chama `PUT /projects/{id}/transcript` com o body correto.

- [ ] **Step 2: Executar teste e verificar falha**

Run: `npm --prefix desktop run test:run -- tests/projects-api.test.ts`
Expected: FAIL método inexistente.

- [ ] **Step 3: Adicionar `updateTranscript` em `desktop/src/api/projects.ts` e exportar em `desktop/src/api.ts`**

- [ ] **Step 4: Executar teste e verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/projects-api.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add desktop/src/api/projects.ts desktop/src/api.ts
git commit -m "feat(desktop): add updateTranscript client API method"
```

---

### Task 5: Desktop - Interface do Editor de Legendas no `TranscriptPanel.vue`

**Files:**
- Modify: `desktop/src/components/TranscriptPanel.vue`
- Modify: `desktop/src/components/ProjectWorkspace.vue` (passar projectId e emit/callback se necessário)
- Modify: `desktop/src/App.vue`
- Test: `desktop/tests/transcript-editing.test.ts`

**Interfaces:**
- Produces: Modo de edição por segmento no `TranscriptPanel.vue` com botões de editar, salvar e cancelar, com tecla `Esc` e `Enter`.

- [ ] **Step 1: Escrever teste de UI para edição de segmento**

```typescript
// desktop/tests/transcript-editing.test.ts
import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import TranscriptPanel from '../src/components/TranscriptPanel.vue';

it('enters edit mode on segment action, saves change and emits update', async () => {
  const onSave = vi.fn().mockResolvedValue(true);
  const w = mount(TranscriptPanel, {
    props: {
      projectId: 'p1',
      transcript: {
        words: [],
        segments: [{ id: 's1', text: 'Texto original', start_us: 1000, end_us: 2000 }]
      },
      sourceUrl: '/source.mp4',
      wordCount: 2,
    },
    // Mock save handler
  });
  const editBtn = w.get('[data-action=edit-segment]');
  await editBtn.trigger('click');
  expect(w.find('textarea.segment-editor-input').exists()).toBe(true);
  const textarea = w.get('textarea.segment-editor-input');
  await textarea.setValue('Texto modificado');
  await w.get('[data-action=save-segment]').trigger('click');
  await flushPromises();
  // Verifica atualização
});
```

- [ ] **Step 2: Executar teste para verificar falha**

Run: `npm --prefix desktop run test:run -- tests/transcript-editing.test.ts`
Expected: FAIL elemento `[data-action=edit-segment]` não encontrado.

- [ ] **Step 3: Implementar UI de edição em `desktop/src/components/TranscriptPanel.vue`**

- Adicionar estado `editingSegmentId = ref<string | null>(null)` e `editingText = ref('')`.
- Adicionar botão com ícone de edição que aparece em hover/focus no item.
- Ao clicar em editar, inicializa o `textarea` com o texto do segmento.
- Ao salvar: chama a API `api.updateTranscript`, atualiza o estado reativo local, fecha o modo de edição e emite notificação toast.
- Ao cancelar (`Esc` ou botão): fecha sem salvar.

- [ ] **Step 4: Executar testes para verificar aprovação**

Run: `npm --prefix desktop run test:run -- tests/transcript-editing.test.ts tests/transcript-panel.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add desktop/src/components/TranscriptPanel.vue desktop/tests/transcript-editing.test.ts
git commit -m "feat(desktop): add inline segment caption editing in TranscriptPanel"
```

---

### Task 6: Verificação de Integração Completa e Build

- [ ] **Step 1: Executar validação de tipos do Vue/TypeScript**
Run: `npm --prefix desktop run check`
Expected: 0 errors.

- [ ] **Step 2: Executar toda a suíte de testes do Vitest**
Run: `npm --prefix desktop run test:run`
Expected: All tests pass.

- [ ] **Step 3: Executar a suíte de testes do pytest**
Run: `pytest -m "not real_media" -q`
Expected: All backend tests pass.

- [ ] **Step 4: Executar build de produção do desktop**
Run: `npm --prefix desktop run build`
Expected: Build success.
