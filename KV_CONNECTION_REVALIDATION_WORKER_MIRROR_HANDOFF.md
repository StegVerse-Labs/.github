# KV Connection Revalidation Worker Mirror Handoff

Status: SOURCE_LANE_OPEN / IMPLEMENTATION_IN_PROGRESS
Repository: `StegVerse-Labs/.github`
Issue: #366
Branch: `feature/kv-connection-revalidation-worker`
Updated: 2026-08-28
Authority effect: NONE
Credential authority: TV/TVC
Production execution authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Provide the sovereign/resident machine-execution surface that restores an exact Personal KV connection assembly to `VERIFIED` only after separately produced provider/source conformance and private-KV readback proofs satisfy the canonical continuity-vault-kit revalidation contract.

Canonical flow:

```text
existing provider/session lane
 -> non-secret provider conformance proof

private KV persistence/readback lane
 -> non-secret KV readback proof

both proofs
 -> resident connection revalidation worker
 -> continuity-vault-kit proof admission
 -> existing verify_connection transition
 -> updated private connection registry
 -> VERIFIED health receipt
```

## Hard boundaries

1. GitHub Actions may validate source only and cannot perform live revalidation.
2. The worker must run on an admitted sovereign/resident StegVerse worker surface.
3. It performs no provider network access.
4. It performs no provider login, MFA, OAuth exchange, token refresh, or SKAP resolution.
5. It accepts no provider password, token, API key, cookie, private key, recovery material, or reusable credential.
6. Provider conformance proof and KV readback proof must already exist and be non-secret.
7. Exact locally materialized `StegVerse-Labs/continuity-vault-kit` source is required.
8. Exact private KnowledgeVault root is required.
9. The worker may mutate only the canonical private KV connection registry/health evidence through continuity-vault-kit runtime helpers.
10. Stale proof relative to the invalidation/recovery event fails closed.
11. The worker may not create or infer proof.
12. Provider operation authority remains NONE.

## Initial machine surfaces

- `KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md`
- `handoffs/KV-CONNECTION-REVALIDATION-001.json`
- `control/worker-registry.d/kv-connection-revalidation-001.json`
- `control/process-worker-adapters.d/kv-connection-revalidation-001.json`
- `cost-basis/worker-runtime/kv-connection-revalidation.json`
- `control/admissible-existence-retrospective-conformance.d/kv-connection-revalidation-001.json`
- `workers/kv_connection_revalidation_worker.py`
- `tests/test_kv_connection_revalidation_worker.py`
- `scripts/check_kv_connection_revalidation_worker.py`

## Admission dependencies

- `SHWP-DURABLE-RUNTIME-ACTIVATION:COMPLETED`;
- merged continuity-vault-kit revalidation proof contract;
- exact local continuity-vault-kit source;
- private KV root;
- conformance proof;
- readback proof;
- current connection assembly in private KV.

## Completion

The worker is terminal only when canonical proof admission succeeds, the exact assembly persists as `VERIFIED`, and its non-secret connection-health receipt persists inside the private KV.

## Current boundary

Source lane only. No live proof consumption, private KV mutation, provider session, or connection verification is claimed by this branch.
