# KV Connection Revalidation Worker Mirror Handoff

Status: SOURCE_LANE_OPEN / IMPLEMENTATION_IN_PROGRESS
Repository: `StegVerse-Labs/.github`
Issue: #366
Branch: `feature/kv-connection-revalidation-worker-366`
Updated: 2026-08-29
Authority effect: NONE
Credential authority: TV/TVC
Production execution authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Add the sovereign/resident WorkerCoordinator task that consumes already-produced non-secret provider conformance and private-KV readback proofs and restores one exact Personal KV connection assembly to `VERIFIED` through the canonical `StegVerse-Labs/continuity-vault-kit` revalidation contract.

Canonical flow:

```text
provider/session conformance proof + private-KV readback proof
 -> admitted resident revalidation worker
 -> exact local continuity-vault-kit runtime
 -> admit_revalidation(...)
 -> canonical verify_connection transition
 -> updated private KV connection registry
 -> connection-health receipt persistence
```

## Hard boundaries

1. GitHub Actions may validate source only; production revalidation requires an admitted sovereign/resident worker.
2. The worker performs no provider network access, provider login, SKAP resolution, or credential retrieval.
3. Passwords, tokens, API keys, private keys, cookies, reusable authentication material, and SKAP secret material are prohibited inputs/environment.
4. Exact locally materialized `StegVerse-Labs/continuity-vault-kit` source is required.
5. Exact private-KV registry binding is required.
6. Conformance and readback proofs must bind the same exact assembly.
7. Stale proofs relative to the required invalidation/recovery timestamp fail closed.
8. The worker consumes proofs; it must not manufacture, infer, or upgrade provider/session/readback evidence.
9. Only the canonical CVK `admit_revalidation`/`verify_connection` path may restore `VERIFIED`.
10. Persisted output remains under `_System/Connections/**` with provider-operation authority `NONE` and credential material absent.

## Required source

- `KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md`
- `handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json`
- `control/worker-registry.d/kv-connection-revalidation-worker-001.json`
- `control/process-worker-adapters.d/kv-connection-revalidation-worker-001.json`
- `workers/kv_connection_revalidation_worker.py`
- `tests/test_kv_connection_revalidation_worker.py`
- `scripts/check_kv_connection_revalidation_worker.py`

## Admission dependencies

- sovereign resident worker runtime genuinely active;
- exact local CVK source containing `runtime/connection_revalidation.py` and `runtime/connection_registry_store.py`;
- private KV root with canonical `Connection_Assemblies.json`;
- one explicit assembly id;
- one non-secret conformance proof and one non-secret readback proof already produced by their separately governed sources;
- optional required-after timestamp supplied when recovery/invalidation freshness must be enforced.

## Completion predicates

Repository/source completion requires:

- hosted/credential-bearing environments rejected;
- required local CVK/private-KV/proof bindings enforced;
- exact assembly lookup required;
- proof schemas and assembly binding delegated to canonical CVK revalidation code;
- stale proof floor enforced;
- verified assembly persisted only after canonical admission succeeds;
- health receipt persisted only after canonical admission succeeds;
- provider operation/network/credential authority remains NONE;
- deterministic tests and static checker pass;
- WorkerCoordinator handoff/registry/process adapter installed;
- exact-head validation observed before merge.

## Runtime completion boundary

Repository/source completion does not prove live provider conformance, private-KV readback, or resident execution. Authentic runtime completion additionally requires an admitted resident claim plus real proofs and inspectable private-KV persistence evidence.
