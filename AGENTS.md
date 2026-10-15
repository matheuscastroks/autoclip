# Repository Guidelines

## Project Structure

AutoClip is a local-first desktop editor with three layers. `engine/` contains the Python 3.12 media pipeline, API, provider adapters, contracts, and rendering code. `desktop/src/` contains the Vue 3/TypeScript interface; `desktop/src-tauri/` wraps it in Tauri 2. Python tests live in `tests/`, frontend tests in `desktop/tests/`, operational helpers in `scripts/`, and architecture/runbooks in `docs/`. Treat `.autoclip/`, `.runtime-tmp/`, `poc-projects/`, `poc-results/`, build output, media, and models as generated or local data, not source.

More specific instructions in `engine/AGENTS.md`, `desktop/AGENTS.md`, and `research/AGENTS.md` override this guide within those directories.

## Build, Test, and Development Commands

- `pip install -e ".[dev,desktop]"` installs the Python engine and development dependencies.
- `pytest -m "not real_media" -q` runs the normal backend suite without opt-in media tests.
- `npm ci --prefix desktop` installs the locked frontend dependencies.
- `npm --prefix desktop run check` type-checks Vue and TypeScript.
- `npm --prefix desktop run test:run` runs Vitest once.
- `npm --prefix desktop run build` creates the frontend production bundle.
- `npm --prefix desktop run desktop:build:local` builds the local debug Tauri executable.

Use Python 3.12 and consult `docs/poc-runbook.md` or `docs/tauri-runbook.md` before running media or desktop workflows.

## Style and Testing

Follow `.editorconfig` and existing language conventions. Keep Python modules and tests in `snake_case`; use PascalCase Vue components, `useX` composables, and camelCase TypeScript identifiers. Frontend formatting is enforced by Prettier and ESLint. Avoid drive-by reformatting.

Add focused regression tests near the affected subsystem. Media, provider, concurrency, and resume changes need failure-path coverage. UI work must cover loading, empty, disabled, and error states. Never describe real-media, visual, or external-provider behavior as validated unless that check actually ran.

## Commits, Pull Requests, and Security

Use the repository's concise conventional subjects, for example `fix(desktop): preserve clip selection`. Keep commits focused. Pull requests should explain the change, list exact verification commands, link relevant issues or design documents, and include screenshots or recordings for visible UI changes.

Never commit API keys, authenticated URLs, videos, transcripts, local databases, generated renders, or model files. Preserve human editorial approval gates and the rule that remote AI receives text only unless the project documentation explicitly changes that contract.
