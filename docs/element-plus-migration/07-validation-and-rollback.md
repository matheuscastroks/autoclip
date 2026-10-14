# AutoClip — Estratégia de Validação, Gates de Aprovação e Rollback

## 1. Filosofia de Garantia de Qualidade

A migração de interface do AutoClip não pode comprometer a estabilidade do fluxo de edição local. Um erro visual pode ser tolerado durante desenvolvimento, mas um bloqueio na comunicação com o motor FastAPI em loopback, um travamento na seleção de arquivos nativos (`rfd`) ou uma falha de renderização na WebView2 inviabilizaria o uso do aplicativo desktop.

Por isso, a validação é estruturada em **5 camadas consecutivas**:

```
Camada 1: Checagem Estática de Tipos (vue-tsc)
    ▼
Camada 2: Testes Unitários de Componente (Vitest + JSDOM Mocks)
    ▼
Camada 3: Build de Produção do Frontend (Vite)
    ▼
Camada 4: Testes de Regressão da API do Motor (Pytest)
    ▼
Camada 5: Empacotamento Desktop e Execução Real (Tauri 2 + WebView2)
```

---

## 2. Matriz de Comandos de Validação

| Camada | Ferramenta / Comando | O que valida | Tolerância a Falhas |
|---|---|---|---|
| **L1: Tipos** | `npm --prefix desktop run typecheck` | Tipagem de props, eventos emits, interfaces do Element Plus | 0 erros permitidos |
| **L2: Frontend** | `npm --prefix desktop run test:unit` | Renderização de componentes, reatividade de estado, mocks | 100% dos 90+ testes devem passar |
| **L3: Bundle** | `npm --prefix desktop run build` | Resolução de assets, tree-shaking, CSS scoping, imports | Build com exit code 0 |
| **L4: Backend** | `.venv/Scripts/pytest tests/unit tests/api` | Integridade das rotas `/api/projects`, `/api/pipeline`, etc. | 100% dos 189 testes devem passar |
| **L5: Desktop** | `npm --prefix desktop run tauri build -- --debug` | WebView2 do Windows, permissões de IPC, renderização nativa | Janela abre e comunica com sidecar |

---

## 3. Mocks Críticos para o Vitest (`desktop/src/test/setup.ts`)

Componentes avançados do Element Plus (como `ElTable`, `ElScrollbar`, `ElSelect` e `ElDrawer`) dependem de APIs do DOM que não existem por padrão no ambiente Node.js / JSDOM.

Para garantir que a suíte de testes do Vitest execute sem falhas artificiais, o arquivo [desktop/src/test/setup.ts](file:///C:/Users/Matheus/Projects/autoclip-editor/desktop/src/test/setup.ts) deve conter os seguintes mocks declarados antes da inicialização dos testes:

```typescript
// desktop/src/test/setup.ts (extensão para Element Plus)
import { vi } from 'vitest';

// 1. Mock de ResizeObserver (obrigatório para ElTable e ElScrollbar)
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// 2. Mock de IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// 3. Mock de window.matchMedia (obrigatório para ElConfigProvider e media queries)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// 4. Mock do ElNotification para inspecionar chamadas de feedback sem renderizar no DOM
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>();
  return {
    ...actual,
    ElNotification: vi.fn(),
  };
});
```

---

## 4. Gates de Aprovação por Fase (Checkpoints de PoC)

Cada fase do plano de implementação possui um gate de qualidade formal. Uma fase só é considerada concluída e mesclada na branch de integração se todos os critérios do gate forem atendidos:

### Gate 0: Setup e Tema Escuro
- [ ] `desktop/src/element-theme.css` compila sem alertas.
- [ ] O aplicativo inicializa no dev server exibindo fundo `#0E1013` e destaque `#D97724`.
- [ ] Nenhum componente renderiza com fundo branco acidental ou borda clara em contraste com o tema escuro.
- [ ] Mocks do Vitest configurados; todos os 90 testes passam.

### Gate 1: Notificações e Overlays
- [ ] `notify('success', ...)` e `notify('error', ...)` disparam `ElNotification` com estilo dark.
- [ ] Notificações são exibidas corretamente sobre modais abertos, sem necessidade de hacks de DOM.
- [ ] `AppToaster.vue` é totalmente removido sem deixar referências soltas.

### Gate 2: Primitivos e Purga do Reka UI
- [ ] `AppButton` e `AppSelect` operam com wrappers do Element Plus com total retrocompatibilidade.
- [ ] O pacote `reka-ui` é desinstalado do `package.json`.
- [ ] `npm --prefix desktop run build` tem sucesso e o tamanho do bundle é inspecionado.

### Gate 3: Modais e Shell Global
- [ ] `ProjectModal` abre via `ElDialog`, validação de formulário impede submissão sem URL ou arquivo.
- [ ] O seletor de arquivos dispara `api.pick('video')` e preserva o caminho local do Windows (`C:\...`).
- [ ] `GlobalQueueDrawer` abre e fecha via `ElDrawer` sem bloquear cliques na tela principal quando recolhida.

### Gate 4: Telas Complexas (Análise e Revisão)
- [ ] `AnalysisPanel.vue` foi refatorado nos 5 subcomponentes dedicados; nenhum arquivo ultrapassa 400 linhas.
- [ ] A seleção de cortes na análise reflete instantaneamente nos contadores e na visualização de transcrição.
- [ ] A tabela de cortes em `ReviewPanel.vue` permite seleção múltipla e exportação sem travar a interface.
- [ ] O player de vídeo 9:16 funciona com preview correto do corte.

### Gate 5: Configurações, Build Desktop e Homologação Final
- [ ] `SettingsPanel.vue` salva parâmetros de IA (Gemini/OpenRouter) e persiste via API REST.
- [ ] Limpeza final de pacotes obsoletos (`vue-sonner`, etc.) concluída.
- [ ] `npm --prefix desktop run tauri build` gera o executável do Windows com sucesso.
- [ ] Teste de ponta a ponta manual executado no aplicativo desktop: criar projeto ➔ transcrever ➔ analisar ➔ revisar ➔ exportar.

---

## 5. Estratégia de Contingência e Plano de Rollback

Para minimizar riscos operacionais durante a implementação, adota-se um isolamento estrito de branches e pontos de restauração (checkpoints) por fase.

### 5.1 Isolamento de Branch Git
Toda a migração deve ocorrer em uma branch dedicada:
```bash
git checkout -b feature/element-plus-migration poc-openshorts-gemini
```
Nenhum commit da migração deve ser feito diretamente na branch principal (`main` ou `poc-openshorts-gemini`) antes da conclusão do **Gate 5**.

### 5.2 Camada de Compatibilidade em Modo Adaptador (Adapter Pattern)
Os componentes `AppButton.vue` e `AppSelect.vue` servem como amortecedores arquiteturais:
- Durante as Fases 2 a 6, as telas existentes continuam consumindo `<AppButton>` e `<AppSelect>`.
- Caso qualquer tela específica apresente regressão visual ou funcional, apenas o componente interno afetado pode ser revertido, sem desfazer as telas já migradas.

### 5.3 Procedimento de Rollback de Emergência

Se uma fase introduzir um defeito crítico irrecuperável:

#### Cenário A: Reversão de uma Fase Específica
Se o defeito ocorrer durante a Fase 4 (por exemplo, na tabela de projetos):
```powershell
# Reverter apenas os arquivos da Fase 4 para o commit anterior ao início da fase
git checkout HEAD~1 -- desktop/src/components/LibraryView.vue desktop/src/components/ProjectModal.vue
npm --prefix desktop run test:unit
```

#### Cenário B: Abortar a Migração Completa
Se for decidido descontinuar a adoção do Element Plus a qualquer momento antes do merge final:
```powershell
# Retornar imediatamente para a branch estável limpa
git checkout poc-openshorts-gemini

# Restaurar estado exato de dependências se houver arquivos temporários
git clean -fd
npm --prefix desktop install
```
Como nenhuma alteração de schema de banco de dados ou formato de arquivo local é realizada (a migração é 100% confinada ao frontend Vue), o rollback para `poc-openshorts-gemini` é **instantâneo, seguro e sem perda de dados de projetos existentes**.
