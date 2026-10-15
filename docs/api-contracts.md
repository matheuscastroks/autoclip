# Internal API contracts

`engine/contracts/api.py` defines the responses for projects, jobs, analysis/proposals, and revisions. FastAPI validates these routes with `response_model`, and includes the same models in its internal OpenAPI schema. Keep HTTP request models in `engine/api/app.py` and persisted pipeline artifacts in `engine/contracts/models.py`.

The desktop imports these responses through `desktop/src/types.ts`. Do not restore handwritten copies of these interfaces or edit `desktop/src/generated/api.ts` directly.

After changing a response contract, activate the Python environment and run from the repository root:

```sh
python scripts/generate_api_types.py
python scripts/generate_api_types.py --check
pytest tests/api/test_response_contracts.py -q
npm --prefix desktop run check
```

The normal Python test suite checks that the generated file is current. Response models retain unknown metadata for compatibility with older workers, but validate all declared fields and state values. Legacy job rows receive empty metadata defaults, without inventing a processing operation.

`technical_pass` is a technical outcome, separate from `review_status`. Final exports require `technical_pass=true` and `review_status=approved`, with editorial approval bound to the current artifact fingerprint. Missing review is `needs_review`; mismatched or unreadable review is `stale_review`; technically invalid artifacts are `invalid`.

Artifact diagnostics distinguish `not_generated`, `available`, `invalid`, `unavailable`, and `stale`. Invalid reads preserve the original data. A completed analysis must still match the current transcript before it can be used to generate clips.
