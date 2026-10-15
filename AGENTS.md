# Repository Guidelines

## Project Structure & Module Organization

AutoClip is a Vue/Vite application. Keep product code in `src/`, reusable UI in `src/components/`, screens in `src/views/`, and shared state or integrations in the existing store and service modules. Put unchanged static files in `public/`; import bundled images and styles from `src/assets/`. Keep generated media, transcripts, local project data, `dist/`, and dependencies out of version control. Place tests beside their subjects as `*.spec.ts` or in the existing test directory.

## Build, Test, and Development Commands

- `npm install` installs project dependencies.
- `npm run dev` starts the Vite development server with hot reload.
- `npm run build` creates the production bundle in `dist/`.
- `npm run preview` serves the production bundle for a final local check.
- `npm run lint` runs the configured static-analysis rules.
- `npm test` runs the configured test suite.

Use the scripts in `package.json` as the source of truth if a command differs.

## Coding Style & Naming Conventions

Follow existing Vue Single-File Component and TypeScript patterns. Use two-space indentation and let the configured formatter decide semicolons and quotes. Name components in PascalCase (`ClipInspector.vue`), composables with a `use` prefix (`useProjectQueue.ts`), and variables/functions in camelCase. Prefer typed props and emits, small components, and shared Element Plus controls. Keep user-facing Brazilian Portuguese consistent with the current interface.

## Testing Guidelines

Add focused tests for parsing, timing calculations, state transitions, and error recovery. Name tests after observable behavior. Before opening a pull request, run tests, linting, and a production build. For UI changes, manually exercise the affected workflow and check loading, empty, error, and disabled states. Follow any coverage threshold defined by repository configuration.

## Commit & Pull Request Guidelines

Write concise, imperative commit subjects, optionally scoped: `fix(editor): preserve clip selection`. Keep commits focused. Pull requests should explain the problem and solution, list verification commands, link relevant issues, and include screenshots or a recording for visible changes. Call out configuration changes, new dependencies, and media-processing impact.

## Security & Configuration

Never commit API keys, local media, transcripts, or generated output. Store secrets in ignored environment files and document variable names in an example file without real values. Sanitize filenames and validate paths before invoking local tools.
