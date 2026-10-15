# Research Workspace Guidelines

## Purpose and Boundaries

This directory contains investigation scripts, benchmarks, environment inventories, upstream snapshots, local models, media, and generated results. It supports technical decisions but is not production engine code. Move reusable product behavior into `engine/` with normal tests instead of importing research scripts into runtime paths.

Treat `snapshots/` as evidence of specific upstream revisions, not editable forks. Keep downloaded media, model weights, virtual environments, benchmark output, and pytest temporary directories out of commits. Public availability is not proof of redistribution rights.

## Reproducible Research

Each new experiment should record its purpose, inputs, exact command, dependency versions, relevant commit or model identifiers, and output location. Use deterministic inputs or hashes where practical. Distinguish clearly between inventory, static inspection, synthetic tests, real-media execution, and human editorial evaluation; one does not substitute for another.

Use `benchmark-requirements.lock.txt` for the research environment when applicable. Prefer the existing scripts for environment probing, media preparation, ASR benchmarking, snapshot auditing, and deliverable verification rather than duplicating them. Keep transient results under ignored result or temporary directories.

## Safety and Validation

Do not download media, call paid or quota-limited providers, or replace large models unless the task explicitly requires it. Never place API keys in scripts, notebooks, JSON results, command examples, or logs. Verify licenses and provenance before adding third-party code, fonts, models, or media.

Research conclusions must link to reproducible evidence and state limitations. A successful command confirms only that execution; do not generalize it into quality, performance, licensing, or production-readiness claims without the corresponding checks.
