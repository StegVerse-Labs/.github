# Canonical work projection requests

A file here asks `.github/workflows/canonical-work-projection-trigger.yml` to
apply one admitted CanonicalWork projection to canonical task state. The push
that lands it on `main` starts the run, the way
`.stegverse/governance-decision-requests/` starts
`organization-governance-decision.yml`. Landing a request is the authority
boundary; the request itself grants nothing.

One request per push, named `<request_id>.json`:

```json
{
  "schema": "stegverse.canonical-work-projection-request/v1",
  "request_id": "cwp-<task>-<n>",
  "task_id": "<existing canonical task id>",
  "observed_registry_generation": 319,
  "hb_epoch": "<ASCII digits, value >= 32>",
  "ingress_receipt": { "schema": "stegverse.canonical-work-intr-materialization-ingress/v1", "...": "..." },
  "consumption_receipt": { "schema": "stegverse.canonical-work-intr-materialization-consumption/v1", "...": "..." },
  "authority_effect": "NONE_REQUEST_ONLY"
}
```

- The receipts are the ones `scripts/consume_canonical_work_intr_materialization_request.py`
  binds; `scripts/apply_admitted_canonical_work_projection.py` validates them unchanged.
- `observed_registry_generation` must equal the live `data/canonical-task-registry.json`
  generation. The projection sets `generation + 1` itself, and
  `scripts/check_registry_generation_fence.py` must ALLOW it.
- The projection only updates an existing task. Registering a new Goal row is a
  separate transition.
- Every decision is recorded on `refs/stegverse/organization-ledger`. A refusal
  carries the six fields: `failure_code`, `failed_predicate`,
  `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal`, `next_attempt`.
- Check a request before committing it:
  `python scripts/canonical_work_projection_trigger.py evaluate --mode plan --request <path>`.
