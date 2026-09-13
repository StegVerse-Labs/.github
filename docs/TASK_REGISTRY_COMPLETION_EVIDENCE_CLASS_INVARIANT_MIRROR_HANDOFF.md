# Task Registry Completion Evidence-Class Invariant

Updated: 2026-09-12
Scope: ALL_CANONICAL_TASKS_EXISTING_AND_NEW

## Rule

A completion statement must identify the evidence class actually proven. The canonical order is:

`SOURCE_IMPLEMENTED -> MERGED -> CI_VALIDATED -> SANDBOX_RUNTIME_OBSERVED -> EXTERNAL_PROVIDER_OBSERVED -> MASTER_RECORDS_RECONSTRUCTED -> END_TO_END`

A stronger class may not be inferred from a weaker class. Bare `complete` / `completed` may not be used for a Goal Task unless its declared terminal evidence class is satisfied.

Historical completion claims that predate contract `v1` remain provenance only. Without an explicit evidence class and evidence references they are `LEGACY_UNQUALIFIED_NON_AUTHORITATIVE`; they cannot satisfy a current terminal predicate or support user-facing completion language.

## Enforcement

- `data/task-registry-global-invariants.json`
- `scripts/validate_task_registry_global_invariants.py`
- `scripts/validate_completion_evidence_v1.py`
- `tests/test_completion_evidence_v1.py`

New or reconciled completion claims using contract `v1` require an allowed evidence class and evidence references. A declared terminal evidence class must be met or exceeded by native evidence from that class. `end_to_end_complete=true` requires `END_TO_END`.

This is coordination/evidence policy only. It grants no execution, transition, credential, provider, custody, reconstruction, or publication authority.

## Evidence status of this change

Current status before repository validation: `SOURCE_IMPLEMENTED` candidate only. `CI_VALIDATED` requires exact-head required validation lanes to pass. `MERGED` requires an observed merge. No sandbox/runtime or stronger class is inferred.

Human action: None.
