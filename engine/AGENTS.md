# Python Engine Guidelines

## Scope and Architecture

This directory implements the Python 3.12 media engine. Keep provider-specific code in `adapters/`, HTTP and desktop-session behavior in `api/`, serialized boundaries in `contracts/`, orchestration in `pipeline/`, and media/rendering concerns in `media/` and `render/`. `editorial/` owns review and approval behavior; do not bypass it from pipeline code. Code under `vendor/` is upstream material and should not be casually edited from engine changes.

Preserve the local-first contract: transcription, editing, captions, and rendering run locally. Remote Gemini or OpenRouter integrations receive text, not source media. Credentials belong in the configured keyring or process environment and must never appear in logs, fixtures, or artifacts.

## Development and Tests

- `pip install -e ".[dev,desktop]"` installs the editable package and test/API dependencies.
- `pytest tests/unit -q` runs fast unit coverage.
- `pytest tests/integration -q` runs subsystem integration tests.
- `pytest -m "not real_media" -q` matches the normal CI backend suite.
- `.\.venv\Scripts\autoclip-engine.exe doctor` checks local runtime dependencies on Windows.

Use `pytest` files named `test_*.py`. Add regression coverage for artifact reuse, cancellation, retries, timeouts, invalid provider responses, and partial failures when those paths change. Tests marked `real_media` are opt-in and a skip is not evidence that the real workflow passed.

## Implementation Conventions

Use four-space Python indentation, `snake_case` names, `Path` objects for filesystem boundaries, and explicit Pydantic contracts at API or persisted-data edges. Preserve atomic writes, hashes, resumability, and idempotency; never make a failed stage look successful. Avoid broad exception swallowing and provider fallback that the user did not request. Changes to schemas, CLI arguments, job states, or persisted artifacts require compatibility review and corresponding tests.
