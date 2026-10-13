# OpenRouter Analysis Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar o OpenRouter como provedor alternativo de IA para análise de temas e seleção editorial de cortes no AutoClip, permitindo o uso de modelos gratuitos (`:free`) ou modelos abertos de ponta sem quebrar a pipeline existente.

**Architecture:** Implementar um adapter `OpenRouterAnalyzer` isolado em subprocesso no backend (seguindo o mesmo padrão de segurança, checkpoints e emissão de eventos do `GeminiAnalyzer`), adicionar suporte ao gerenciamento seguro de credenciais via `keyring`, expandir a API de configurações para alternância entre provedores (`gemini` vs `openrouter`) e atualizar a UI de Configurações no desktop.

**Tech Stack:** Python 3.12, `httpx`, `pydantic`, `keyring`, FastAPI/uvicorn, Vue 3, TypeScript, Vitest, Pytest.

**Spec:** Baseado na arquitetura atual de contratos `engine/contracts/models.py`, protocolo `Analyzer` em `engine/adapters/gemini/analyzer.py` e especificações de API da OpenRouter (`https://openrouter.ai/api/v1/chat/completions`).

## Global Constraints

- Manter 100% de integridade dos 81 testes de frontend existentes e dos testes unitários do backend.
- Nunca salvar chaves de API em texto puro no disco ou localStorage; utilizar `keyring` (Windows Credential Manager) ou variáveis de ambiente.
- As respostas da análise devem aderir estritamente ao schema Pydantic `GeminiResponse` (`topics`, `candidates`, validação de `word_id` contra a transcrição da janela).
- A transcrição continua 100% local via `faster-whisper` (não roteada para OpenRouter devido a custo e precisão de legendas por palavra).

## Review Focus

1. **Modelos sem suporte a `json_schema` estrito:** O OpenRouter suporta tanto `response_format: {"type": "json_schema", ...}` quanto `{"type": "json_object"}`. O worker deve lidar com modelos que retornam markdown com bloco ````json ou JSON puro.
2. **Rate limits da versão gratuita (429 / Too Many Requests):** Em caso de limite de taxa do OpenRouter (especialmente nos modelos `:free`), emitir evento `PROVIDER_RATE_LIMIT` amigável com tempo de espera (`Retry-After`).
3. **Persistência de checkpoints:** O cache incremental de janelas já analisadas deve funcionar de forma idêntica entre Gemini e OpenRouter (usando o hash do modelo, prompt e janela).
4. **Alternância fluida na UI:** O usuário deve conseguir alternar entre Gemini e OpenRouter nas Configurações sem perder os dados salvos do outro provedor.
5. **Segurança de credenciais:** O worker do OpenRouter roda isolado em subprocesso com timeout rígido e sem vazar tokens em logs ou rastros de erro.

---

### Task 1: Credenciais e Gerenciamento Seguro da Chave OpenRouter

**Files:**
- Create: `engine/adapters/openrouter/__init__.py`
- Create: `engine/adapters/openrouter/credentials.py`
- Test: `tests/unit/test_openrouter_credentials.py`

- [ ] **Step 1:** Escrever teste unitário para `get_openrouter_key` e `set_openrouter_key` mockando `keyring` e `os.environ`.
- [ ] **Step 2:** Rodar `pytest tests/unit/test_openrouter_credentials.py` e confirmar que falha.
- [ ] **Step 3:** Implementar validação de chave ASCII e persistência segura em `engine/adapters/openrouter/credentials.py`.
- [ ] **Step 4:** Rodar `pytest tests/unit/test_openrouter_credentials.py` e confirmar aprovação (100% verde).

---

### Task 2: Subprocess Worker e Comunicação HTTP com OpenRouter

**Files:**
- Create: `engine/adapters/openrouter/request_worker.py`
- Modify: `engine/pipeline/fingerprints.py`
- Test: `tests/unit/test_openrouter_worker.py`

- [ ] **Step 1:** Escrever teste unitário simulando requisições com mock de `httpx` (respostas válidas com JSON schema, respostas com markdown ````json, erro 429 com Retry-After e erro 401 de autenticação).
- [ ] **Step 2:** Implementar `engine/adapters/openrouter/request_worker.py` compatível com `/api/v1/chat/completions`:
  - Envio de headers `Authorization: Bearer <KEY>`, `HTTP-Referer` e `X-Title`.
  - Envio de payload com `temperature: 0` e `response_format` estruturado.
  - Parser robusto de JSON com sanitização de fenced code blocks.
- [ ] **Step 3:** Atualizar `PACKAGES['analyze']` em `engine/pipeline/fingerprints.py` se necessário.
- [ ] **Step 4:** Rodar `pytest tests/unit/test_openrouter_worker.py` e garantir passagem dos testes.

---

### Task 3: Implementação do `OpenRouterAnalyzer`

**Files:**
- Create: `engine/adapters/openrouter/analyzer.py`
- Test: `tests/unit/test_openrouter_analyzer.py`

- [ ] **Step 1:** Escrever teste unitário de pipeline para `OpenRouterAnalyzer`:
  - Validação de IDs de palavras da transcrição.
  - Gravação e reutilização de checkpoints por janela.
  - Emissão de eventos estruturados no `EventWriter` (`window_started`, `window_reused`, `analysis_started`).
- [ ] **Step 2:** Implementar `OpenRouterAnalyzer` em `engine/adapters/openrouter/analyzer.py` satisfazendo o protocolo `Analyzer`.
- [ ] **Step 3:** Rodar `pytest tests/unit/test_openrouter_analyzer.py` e confirmar aprovação.

---

### Task 4: Integração no Runner, Configurações e API Backend

**Files:**
- Modify: `engine/contracts/models.py`
- Modify: `engine/api/settings.py`
- Modify: `engine/api/job_worker.py`
- Modify: `engine/api/app.py`
- Test: `tests/unit/test_settings_openrouter.py`

- [ ] **Step 1:** Escrever teste de integração para a API de settings (`GET /api/settings`, `POST /api/settings` e endpoint para chave OpenRouter).
- [ ] **Step 2:** Atualizar `engine/api/settings.py` para suportar `ai_provider: 'gemini' | 'openrouter'`, `openrouter_model` e status `openrouter_key_configured`.
- [ ] **Step 3:** Atualizar `engine/api/job_worker.py` para instanciar dinamicamente `OpenRouterAnalyzer` ou `GeminiAnalyzer` com base no `settings['ai_provider']`.
- [ ] **Step 4:** Adicionar rota `POST /api/auth/openrouter-key` em `engine/api/app.py`.
- [ ] **Step 5:** Rodar a suite completa do backend com `pytest` e confirmar aprovação.

---

### Task 5: Interface de Configuração no Desktop (Frontend)

**Files:**
- Modify: `desktop/src/types.ts`
- Modify: `desktop/src/api.ts`
- Modify: `desktop/src/components/SettingsPanel.vue`
- Test: `desktop/tests/openrouter-settings.test.ts`

- [ ] **Step 1:** Atualizar interfaces em `desktop/src/types.ts` (`Config` com `ai_provider`, `openrouter_model`, `openrouter_key_configured`).
- [ ] **Step 2:** Adicionar método `saveOpenRouterKey` em `desktop/src/api.ts`.
- [ ] **Step 3:** Escrever teste Vitest em `desktop/tests/openrouter-settings.test.ts` validando a alternância visual entre os provedores Gemini e OpenRouter e salvamento de chave.
- [ ] **Step 4:** Atualizar `desktop/src/components/SettingsPanel.vue` com seletor de provedor e catálogo de modelos recomendados (ex: `openrouter/free`, `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-chat`).
- [ ] **Step 5:** Rodar `npm test -- --run` no frontend e verificar que todos os 82+ testes passam.

---

### Task 6: Verificação Ponta a Ponta

- [ ] **Step 1:** Rodar `npm --prefix desktop run build` para garantir zero erros de TypeScript e compilação limpa.
- [ ] **Step 2:** Executar um teste de análise usando um projeto existente ou mock para confirmar que o fluxo de eventos e checkpoints opera perfeitamente.
