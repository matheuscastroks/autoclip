# Desktop Application Guidelines

## Scope and Organization

`src/` is the Vue 3 and TypeScript client, `tests/` contains Vitest coverage, and `src-tauri/` contains the Rust/Tauri 2 wrapper. Put reusable UI in `src/components/`, composables in `src/composables/`, domain logic in `src/domain/`, and backend access behind the existing API modules. Keep shared styling in the token, theme, and layout stylesheets rather than introducing isolated visual constants.

The browser UI must not access the filesystem or spawn processes directly. Use authenticated loopback API flows already exposed by the Python engine. Tauri changes must preserve the external-origin, new-window, download, credential, and lifecycle restrictions documented in `docs/tauri-runbook.md`.

## Commands and Quality Gates

Run commands from the repository root:

- `npm ci --prefix desktop` installs locked dependencies.
- `npm --prefix desktop run check` runs `vue-tsc`.
- `npm --prefix desktop run lint` runs ESLint.
- `npm --prefix desktop run format:check` checks Prettier formatting.
- `npm --prefix desktop run test:run` runs Vitest once.
- `npm --prefix desktop run build` type-checks and builds the web client.
- `cargo test --manifest-path desktop/src-tauri/Cargo.toml` runs Rust tests.

## Coding and Testing Conventions

Use two spaces, semicolons, single quotes, a 100-column print width, and trailing commas as configured by Prettier. Name Vue components in PascalCase, composables with a `use` prefix, and TypeScript values in camelCase. Prefer typed props/emits, Element Plus primitives, Lucide icons, and existing design tokens.

Name frontend tests `*.test.ts` and test observable behavior. UI changes should cover loading, empty, disabled, error, polling, and recovery states. Run the targeted test while iterating, then the full check, lint, test, and build gates. Provide screenshots or a short recording for visible changes; DOM tests alone do not establish visual quality.
