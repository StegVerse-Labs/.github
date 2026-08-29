# KV Connection Health Reconciler Mirror Handoff

Status: SOURCE_MERGED_VALIDATED / RESIDENT_ACTIVATION_PENDING
Repository: `StegVerse-Labs/.github`
Issue: #364
Implementation PR: #365
Validated head: `0bbf9a98a507983e9506b6e97f781a10b52017d4`
Merge commit: `6d76796ac08be73e993ac2f6234422bb3d9092d2`
Task-vector integration PR: #402
Task-vector merge: `f258e3e7d6dca999b1a24095495b344e73401742`
Updated: 2026-08-29
Authority effect: NONE
Credential authority: TV/TVC
Production execution authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Close the non-secret machine loop from provider/source change observations into the Personal KV connection assembly registry.

Canonical flow:

```text
resident provider-change observer
 -> stegverse.kv.source-change-observation/v1
 -> resident connection-health reconciler
 -> continuity-vault-kit source-change evaluator
 -> updated private KV connection assembly
 -> connection-health receipt
 -> private KV Health/ persistence
 -> separate revalidation-proof lane when required
```

## Hard boundaries

1. GitHub Actions may validate source only and cannot perform production reconciliation.
2. The reconciler must run on an admitted sovereign/resident StegVerse worker surface.
3. It performs no provider network access.
4. It receives no provider credentials, passwords, tokens, API keys, cookies, private keys, or SKAP material.
5. It does not resolve SKAP.
6. It grants no provider operation authority.
7. Exact locally materialized `StegVerse-Labs/continuity-vault-kit` source is required.
8. A private KnowledgeVault root binding is required.
9. Only `_System/Connections/**` connection-state/evidence paths may be mutated by this task.
10. Malformed observations, missing provider assembly bindings, schema drift, secret-bearing state, or persistence failure fail closed.
11. The reconciler may invalidate stale VERIFIED state but may not independently restore VERIFIED; re-verification still requires provider/source conformance proof plus private-KV readback proof.

## Implemented machine surfaces

- `KV_CONNECTION_HEALTH_RECONCILER_MIRROR_HANDOFF.md`
- `handoffs/KV-CONNECTION-HEALTH-RECONCILER-001.json`
- `control/worker-registry.d/kv-connection-health-reconciler-001.json`
- `control/process-worker-adapters.d/kv-connection-health-reconciler-001.json`
- `control/task-vectors/KV-CONNECTION-HEALTH-RECONCILER-001.json`
- `cost-basis/worker-runtime/kv-connection-health-reconciler.json`
- `workers/kv_connection_health_reconciler_worker.py`
- `tests/test_kv_connection_health_reconciler_worker.py`
- `scripts/check_kv_connection_health_reconciler.py`
- `control/admissible-existence-retrospective-conformance.d/kv-connection-health-reconciler-001.json`

## Validation and integration evidence

PR #365 is merged. Its exact implementation head `0bbf9a98a507983e9506b6e97f781a10b52017d4` produced successful hosted validation evidence:

- Validate organization control plane - No GitHub Token Authority: run `33191931561` SUCCESS
- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: run `33191931584` SUCCESS

PR #402 later projected `KV-CONNECTION-HEALTH-RECONCILER-001` and the provider-change observer into canonical task-vector control, merging as `f258e3e7d6dca999b1a24095495b344e73401742`. The vectorized task preserves independent task-control ownership, exact two-blocker registry/handoff parity, no credentials, no provider-operation authority, no third-party-runtime requirement, and no activation claim.

Hosted validation proves source/control-plane conformance only. It does not prove resident execution or private-KV mutation.

## Admission dependencies

- sovereign resident worker runtime genuinely active;
- locally materialized exact `continuity-vault-kit` source;
- private KV root;
- canonical non-secret source-change observation from the admitted observer;
- connection registry already materialized inside private KV;
- output persistence available under `_System/Connections/**`.

## Remaining machine-execution work

1. Observe an admitted sovereign/resident worker claim for `KV-CONNECTION-HEALTH-RECONCILER-001`.
2. Bind exact local CVK source and the private-KV connection registry.
3. Consume an authentic provider-change observation from `KV-PROVIDER-CHANGE-OBSERVER-001`.
4. Persist the updated assembly and connection-health receipt into the private KV.
5. Prove duplicate observations are idempotently skipped and malformed/secret-bearing observations fail closed.
6. For a material source change, prove stale VERIFIED state is invalidated.
7. Invoke the separate connection-revalidation proof path; do not let this reconciler restore VERIFIED by itself.

## Current boundary

Repository/source implementation, WorkerCoordinator registration, exact-head hosted validation, merge, and canonical task-vector integration are COMPLETE.

Issue #364 is therefore complete for its repository-owned deliverable and may remain closed. Remaining work is authentic resident execution/private-KV evidence, not additional implementation in this issue.

No private KV connection state has been reconciled by this handoff absent inspectable resident runtime evidence.
