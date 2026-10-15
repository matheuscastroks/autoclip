# UI/UX v2 — Phase 2: shell and navigation

## Implementation

- `components/layout/AppRail.vue`: fixed 64px rail, local Fluent icons, accessible command names/tooltips, active-job badge, bottom Settings and engine slot.
- `components/layout/WorkspaceHeader.vue`: shared library/project context, truncated title with full native title, metadata and contextual actions.
- `components/layout/ProjectTabs.vue`: controlled four-destination navigation, reliable counts, existing tab/panel IDs and roving keyboard focus.
- `ProjectWorkspace.vue`: delegates heading/tabs without changing processing or review actions.
- `App.vue`: retains the opened project, selection and active tab across global navigation; explicit back returns to the library. Queue remains outside page transitions. Existing engine disclosure, refresh and shutdown guards remain in App.
- `theme.css`: horizontal shell; removed superseded global-header/navigation styles; repositioned engine disclosure beside the rail. No new important overrides.
- Static icon registry adds Back and Transcript; generated component declarations updated by the existing plugin.

No Python, API contracts, persistence, queue scheduling, Tauri or media-pipeline changes.

## Async navigation decisions

Navigation and project identity have separate generations. A project detail request
abandoned before it opens cannot take over a newer destination. Once its identity
has opened, artifact/selection hydration can finish even while Settings is active.
Explicit back or another project invalidates the previous project generation.

Polling and post-operation reloads use nonactivating project loads: completion of
review, delete, restore or export cannot unexpectedly navigate out of Settings.
Explicit library/queue opening and project creation/import still activate Projects.

Page components unmount on global navigation, releasing players and overlays.
App retains the project tab and domain selection, not every transient local filter.
Cost of this decision: filters/scroll local to an unmounted view reset as before.

## Regression evidence

Observed RED then GREEN:

- Settings → Projects lost the opened project/tab.
- Polling completion forced navigation to Projects.
- Abandoned detail responses reopened a project after navigation (existing test now uses the accessible Settings name, not button position).
- Review finding: navigation during selection hydration lost the result and left media loading pending.
- Review finding: background export completion forced navigation to Projects.

Additional coverage exercises artifact-phase hydration, retained selection, explicit
back, queue accessibility and arrow/Home/End tab selection/focus. An initial missing
component import preceded implementation of the extracted tabs.

## Browser evidence

Actual `App.vue` with disposable local API fixtures, no private projects or paid AI.
Local synthetic video only. All commands still enter the real App handlers; API
boundaries return fixtures. No fixture code is included in the production entry.

Project shell measured at 1920×1080, 1366×768, 1280×720, 1000×680 and 800×600:
64px rail throughout, no document-level horizontal overflow, title truncation and
visible folder action. Visual inspection confirmed the compact 800×600 Cuts view.
The global queue was opened over Settings at 1000×680.

Screenshots under ignored `.runtime-tmp/ui-v2-qa/`:

- `phase2-library-1366x768.png`
- `phase2-project-{width}x{height}.png` (five requested sizes)
- `phase2-settings-1000x680.png`
- `phase2-project-final-1000x680.png` (stable final paint and keyboard focus)
- `phase2-engine-1000x680.png`

Browser journey confirmed Settings → queue → close → Projects returns to the same
Cuts tab. Home/End changed both active tab and focus. Escape closed the engine
disclosure and restored focus to its summary. Badge foreground resolved to
`#16232d` on `#afc6d5` after correcting a token reference during visual QA.

Library row title overlap is inherited and explicitly belongs to Phase 3; shell
overflow measurements do not prove those rows are correctly laid out. Some captures
can precede a transition's final paint; only stable screenshots should be cited as
visual evidence. Tauri/native runtime, OS high contrast, complete media/provider
journeys and real backend job operations were not manually exercised.

## Independent review

One read-only fresh-context review found two Important async navigation issues,
both reproduced and corrected in one fix pass. No Critical findings.

Deferred minor: the queue button's fixed accessible name does not include its
badge count; the visible count is correct. Improve its accessible description in
the final accessibility pass.

Accepted review boundaries: component-local filter reset and media unmount are
intentional; queue independence/tab associations were inspected; source-channel
omission and action relocation fit the approved shell scope. Existing library
overlap and queue-modal focus mechanics remain with their owning phases. Keeping
legacy compatibility CSS costs temporary styling complexity but avoids unrelated
screen regressions. No native/provider guarantees are inferred from these checks.

## Final gates

- `npm --prefix desktop run check`: passed.
- `npm --prefix desktop run lint`: 0 errors, 38 inherited warnings; no new warnings.
- `npm --prefix desktop run format:check`: same 10 inherited files, no changed file failing.
- `npm --prefix desktop run test:run`: **178 passed, 31 files**.
- `npm --prefix desktop run build`: passed; JS 466.67 kB / gzip 156.73, CSS 510.94 kB / gzip 73.68.
- `git diff --check`: passed.

No Python/Rust suite: no shared contracts or native/engine behavior changed.
Hosted CI is distinct from these local commands and was not queried. Screenshots
are browser evidence, not native Tauri validation. No performance gain is claimed.
