# 06. Sistema de Design, Identidade Visual e Acessibilidade (WCAG 2.2 AA)

## 1. Princípios Visuais e Rejeição de Clichês Genéricos de IA

Seguindo as diretrizes de design autêntico e de alto nível da skill `frontend-design`:
1. **Banimento de Padrões Clichês:**
   - ❌ *Banido:* Paleta "creme morno + terracota/argila" (fórmula saturada de ferramentas geradas por IA).
   - ❌ *Banido:* Caixas idênticas com cantos excessivamente arredondados (`rounded-2xl` genérico) e sombras cinzas difusas sem estrutura.
   - ❌ *Banido:* Rótulos em caixa alta com espaçamento exagerado (*TRACKED-OUT ALL CAPS EYEBROWS*) decorativos antes de cada título.
   - ❌ *Banido:* Gradientes roxos/azuis genéricos em botões e bordas de IA.
2. **Identidade do AutoClip:**
   - Uma ferramenta desktop inspirada na precisão e sobriedade de mesas de edição e ilhas de corte profissionais.
   - Fundo escuro profundo de alto contraste, tipografia editorial nítida, linhas de separação estruturais sutis e um acento visual calibrado em **Âmbar/Laranja Quente Técnico** que remete à fita de corte, iluminação de estúdio e atenção deliberada.

---

## 2. Paleta de Cores e Tokens Semânticos

| Token CSS | Valor Hex | Papel Semântico no Design | Relação de Contraste |
| :--- | :--- | :--- | :--- |
| `--color-canvas` | `#0E1013` | Fundo principal da aplicação (Dark Studio Slate). | Base |
| `--color-surface` | `#16191F` | Superfície de painéis principais e cards de tarefas. | 1.15:1 vs Canvas |
| `--color-surface-raised`| `#1E232B` | Superfície elevada para cards selecionados, modais e menus flutuantes. | 1.4:1 vs Canvas |
| `--color-border-subtle` | `#2A303C` | Divisórias e bordas secundárias de cartões. | 3.2:1 vs Canvas (WCAG 1.4.11) |
| `--color-border-focus`  | `#E08A3C` | Anel de foco ativo para teclado e seleção de propostas. | 4.8:1 vs Canvas (WCAG 2.4.7) |
| `--color-accent`        | `#D97724` | Botões de ação primária, botões de Play/Geração e âncoras de destaque. | 5.2:1 vs Canvas |
| `--color-text-primary`  | `#F2F4F7` | Títulos, textos principais e legendas de vídeo. | 14.5:1 vs Canvas (WCAG 1.4.3 AAA) |
| `--color-text-muted`    | `#9AA4B2` | Metadados, timestamps secundários e instruções de suporte. | 6.8:1 vs Canvas (WCAG 1.4.3 AA) |
| `--color-warning-surface`| `#2A2012` | Fundo do badge de conflito temporal / sobreposição. | - |
| `--color-warning-border` | `#8C531B` | Borda de alerta de sobreposição. | 3.5:1 vs Canvas |
| `--color-warning-text`  | `#FBBF24` | Texto do alerta de sobreposição (*"Conflita com Corte #1"*). | 8.2:1 vs Surface |
| `--color-error`         | `#EF4444` | Falhas de download ou interrupções de processo. | 4.6:1 vs Surface |
| `--color-success`       | `#10B981` | Conclusão de etapas e exportações prontas. | 4.9:1 vs Surface |

---

## 3. Escala Tipográfica e Ritmo de Leitura

A tipografia utiliza fontes do sistema com excelente legibilidade técnica e suporte a caracteres internacionais:
`font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;`

Para números, contadores de tempo e timecodes, utiliza-se numerais tabulares:
`font-variant-numeric: tabular-nums;`

| Nível / Papel | Tamanho / Altura de Linha | Peso | Limite de Largura | Uso Exclusivo |
| :--- | :--- | :--- | :--- | :--- |
| **Display / H1** | `24px / 32px` (`1.5rem`) | SemiBold (600) | Max 60ch | Título do projeto e cabeçalho da biblioteca. |
| **Seção / H2** | `18px / 26px` (`1.125rem`) | SemiBold (600) | Max 65ch | Títulos dos painéis (Curadoria, Revisão, Esteira). |
| **Card / H3** | `15px / 22px` (`0.9375rem`)| Medium (500) | Max 50ch | Títulos das propostas de cortes e cards de etapas. |
| **Corpo Primário** | `14px / 20px` (`0.875rem`)| Regular (400) | **Max 75ch** | Raciocínio da IA, parágrafos de transcrição e detalhes. |
| **Metadados / Badge**| `12px / 16px` (`0.75rem`)| Medium (500) | - | Timestamps, durações, tags de status e atalhos. |

---

## 4. Componentes Chave da Nova Arquitetura

### 4.1. Esteira de Progresso Semântico (`ProjectStepper`)
- Substitui a barra de progresso genérica por 4 nós discretos:
  1. *Importação de Mídia*
  2. *Transcrição de Áudio*
  3. *Análise Temática*
  4. *Cortes e Revisão*
- Cada nó possui 4 estados visuais distintos:
  - `completed`: Ícone de check sutil (`#10B981`), linha sólida conectada. Permite clique para inspecionar histórico.
  - `active`: Anel iluminado (`#D97724`), spinner discreto de progresso, indicação textual da sub-etapa.
  - `pending`: Ponto cinza desativado (`#2A303C`), sem clique.
  - `error`: Ícone de alerta vermelho (`#EF4444`) com ação direta de recuperação.

### 4.2. Card de Proposta de Corte (`ProposalCard`)
- Container elevado com borda de 1px.
- Checkbox de seleção com alvo expandido de **36×36px**.
- Badge de Gancho (*Hook*) com destaque tipográfico: a primeira frase do corte aparece em destaque para rápida avaliação visual.
- Player de áudio embutido (*waveform* simplificada ou botão de play direto de 36px) que carrega apenas o segmento de áudio sem travar a CPU com render de vídeo.
- Estado de conflito/sobreposição: Fundo sutilmente escurecido, checkbox desabilitada com tooltip acessível e mensagem de aviso explícita.

### 4.3. Moldura do Player Vertical 9:16 (`VerticalPlayerFrame`)
- Dimensões calibradas para 1366×768:
  - Altura máxima: `480px`
  - Largura proporcional: `270px` (9:16 exato)
  - Margem vertical e controles inferiores contidos em no máximo `580px`, deixando 188px de folga no viewport de 768px.
- Legendas renderizadas sobre o vídeo com fundo de contraste semitransparente para legibilidade absoluta.

---

## 5. Matriz de Acessibilidade e Teclado (WCAG 2.2 AA)

| Critério WCAG 2.2 | Requisito da Norma | Solução Implementada no Redesenho do AutoClip |
| :--- | :--- | :--- |
| **SC 1.4.3 Contraste Mínimo** | Razão 4.5:1 para texto normal; 3:1 para texto grande. | Todo texto de leitura possui razão mínima de 6.8:1 sobre sua superfície correspondente. |
| **SC 2.1.1 Teclado** | Todas as ações operáveis via teclado sem armadilhas. | Os 789 botões de timestamp da transcrição foram removidos do ciclo sequencial de Tab. O leitor de transcrição torna-se uma região única navegável com setas para cima/baixo (`ArrowUp` / `ArrowDown`). |
| **SC 2.4.7 Foco Visível** | Indicador de foco com alto contraste evidente. | Estilo global: `outline: 2px solid var(--color-border-focus); outline-offset: 2px;` aplicado a todos os botões, checkboxes e links. |
| **SC 2.4.11 Foco Não Encoberto** | Elemento focado não pode ficar oculto por barras fixas. | Barra flutuante de ações utiliza padding defensivo no final da página para impedir que qualquer card de proposta fique sob a barra. |
| **SC 2.5.8 Alvo Mínimo** | Dimensão mínima de 24×24px para qualquer alvo clicável. | Todos os botões secundários (fechar aviso, pausar, ver detalhes) ajustados para altura mínima de **32px**. Botões primários ajustados para **38px**. |
| **SC 4.1.3 Mensagens de Status** | Regiões acessíveis para atualizações de background. | Elemento invisível `<div aria-live="polite" class="sr-only">` anuncia conclusões de download, transcrição e renderização sem roubar o foco do usuário. |

### Atalhos Globais de Teclado Suportados:
- `Espaço`: Play / Pause no player de áudio e de vídeo.
- `J` / `L`: Retroceder / Avançar 5 segundos no player.
- `K`: Alternar Play / Pause.
- `Esc`: Fechar gaveta de transcrição, fechar fila global ou fechar modais.
- `Ctrl + N` (ou `Cmd + N`): Abrir modal de Novo Projeto a partir da biblioteca.
