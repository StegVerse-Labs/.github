# KV Connection Health Reconciler Mirror Handoff

Status: SOURCE_LANE_OPEN / IMPLEMENTATION_IN_PROGRESS
Repository: `StegVerse-Labs/.github`
Issue: #364
Branch: `feature/kv-connection-health-reconciler`
Updated: 2026-08-28
Authority effect: NONE
Credential authority: TV/TVC
Production execution authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Close the machine loop from non-secret provider/source change observations into the Personal KV connection assembly registry.

Canonical flow:

```text
resident provider-change observer
 -> stegverse.kv.source-change-observation/v1
 -> resident connection-health reconciler
 -> continuity-vault-kit source-change evaluator
 -> updated private KV connection assembly
 -> connection-health receipt
 -> private KV Health/ persistence
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
11. The reconciler may invalidate stale VERIFIED state but may not independently restore VERIFIED; re-verification still requires connection proof plus KV readback proof.

## Initial machine surfaces

- `KV_CONNECTION_HEALTH_RECONCILER_MIRROR_HANDOFF.md`
- `handoffs/KV-CONNECTION-HEALTH-RECONCILER-001.json`
- `control/worker-registry.d/kv-connection-health-reconciler-001.json`
- `control/process-worker-adapters.d/kv-connection-health-reconciler-001.json`
- `cost-basis/worker-runtime/kv-connection-health-reconciler.json`
- `workers/kv_connection_health_reconciler_worker.py`
- `tests/test_kv_connection_health_reconciler_worker.py`

## Admission dependencies

- `SHWP-DURABLE-RUNTIME-ACTIVATION:COMPLETED`;
- locally materialized continuity-vault-kit exact source;
- private KV root;
- non-secret source-change observation file/directory;
- connection registry already materialized inside private KV.

## Current boundary

Source lane only. No private KV connection state has been reconciled by this branch and no resident execution is claimed.
