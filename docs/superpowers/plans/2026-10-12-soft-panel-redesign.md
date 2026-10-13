# Soft panel redesign implementation

Approved input: docs/soft-panel-redesign-proposal.md and user instruction to implement. Execute inline, as established in this session.

1. Replace accumulated theme imports with semantic tokens, a consolidated functional layout stylesheet and a soft-panel theme; retain component contracts and keyboard behavior.
2. Replace wide global sidebar with top navigation and an engine status disclosure; preserve refresh/shutdown and local session information. Keep compact project identity, rename overview label Preparação.
3. Apply consistent panels/tables/forms/menus/toasts and contextual analysis/review layout across existing screens. Do not alter engine/provider calls or export guards.
4. Verify Vue tests, build, browser viewports and selection; compile native shell with updated assets. Record native visual limitations separately. Commit source and evidence.

Ruling: Implement directly against approved proposal; no extra design mockup gate, since user explicitly requested implementation. The established inline method persists. Preview the real UI with existing data, without new analysis/render/provider calls.

Completed: steps 1–4. Validation: 65 Vue tests passed, frontend and local Tauri builds passed, browser captures recorded. Native visual inspection remains pending; see docs/soft-panel-redesign-validation.md.
