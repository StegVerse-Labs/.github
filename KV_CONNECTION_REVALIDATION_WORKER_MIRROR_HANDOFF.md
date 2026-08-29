# KV Connection Revalidation Worker Mirror Handoff

Status: SOURCE_MERGED_VALIDATED / RESIDENT_ACTIVATION_PENDING
Repository: `StegVerse-Labs/.github`
Issue: #366
Implementation PR: #417
Validated head: `a39f29ab01688a40bc855dbc033c520744bfe335`
Merge commit: `6db36604bb1c2dfbecd6311807e3385d6193b3ec`
Updated: 2026-08-29
Authority effect: NONE
Credential authority: TV/TVC
Production execution authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Provide the sovereign/resident WorkerCoordinator task that consumes already-produced non-secret provider conformance and private-KV readback proofs and restores one exact Personal KV connection assembly to `VERIFIED` through the canonical `StegVerse-Labs/continuity-vault-kit` revalidation contract.

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

## Implemented source

- `KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md`
- `handoffs/KV-CONNECTION-REVALIDATION-WORKER-001.json`
- `control/worker-registry.d/kv-connection-revalidation-worker-001.json`
- `control/process-worker-adapters.d/kv-connection-revalidation-worker-001.json`
- `control/admissible-existence-retrospective-conformance.d/kv-connection-revalidation-worker-001.json`
- `workers/kv_connection_revalidation_worker.py`
- `tests/test_kv_connection_revalidation_worker.py`
- `scripts/check_kv_connection_revalidation_worker.py`
- `control/cosv-global-registry-coverage.json` denominator reconciliation

## Validation and merge evidence

PR #417 merged successfully as `6db36604bb1c2dfbecd6311807e3385d6193b3ec` after exact-head validation of `a39f29ab01688a40bc855dbc033c520744bfe335`.

Exact-head hosted validation:

- Heartbeat Worker Project - Validation Only / No GitHub Token Authority: run `33272935395` SUCCESS
- Validate organization control plane - No GitHub Token Authority: run `33272935396` SUCCESS

The earlier validation defects were repaired before merge: the new task received required Admissible-Existence retrospective conformance classification, and the live COSV worker denominator was reconciled from 56 to 57 with this task explicitly active/unvectorized. Hosted validation proves source/control-plane conformance only and does not prove resident execution.

## Admission dependencies

- sovereign resident worker runtime genuinely active;
- exact local CVK source containing `runtime/connection_revalidation.py` and `runtime/connection_registry_store.py`;
- private KV root with canonical `Connection_Assemblies.json`;
- one explicit assembly id;
- one non-secret conformance proof and one non-secret readback proof already produced by their separately governed sources;
- optional required-after timestamp supplied when recovery/invalidation freshness must be enforced.

## Repository/source completion predicates

- hosted/credential-bearing environments rejected: SATISFIED;
- required local CVK/private-KV/proof bindings enforced: SATISFIED;
- exact assembly lookup required: SATISFIED;
- proof schemas and assembly binding delegated to canonical CVK revalidation code: SATISFIED;
- stale proof floor enforced: SATISFIED;
- verified assembly persisted only after canonical admission succeeds: SATISFIED;
- health receipt persisted only after canonical admission succeeds: SATISFIED;
- provider operation/network/credential authority remains NONE: SATISFIED;
- deterministic tests and static checker pass: SATISFIED;
- WorkerCoordinator handoff/registry/process adapter installed: SATISFIED;
- exact-head validation observed before merge: SATISFIED.

## Remaining machine-execution work

1. Project `KV-CONNECTION-REVALIDATION-WORKER-001` into canonical COSV task-vector control; it is currently deliberately visible as active/unvectorized rather than silently omitted.
2. Observe an admitted sovereign/resident claim for the task.
3. Bind exact local CVK source and the private-KV connection registry.
4. Consume authentic provider conformance and private-KV readback proofs from their separately governed producers.
5. Persist/read back the resulting VERIFIED assembly and health receipt.
6. Preserve the two runtime blockers until inspectable evidence exists: sovereign runtime proof and authentic proof-pair/private-KV execution evidence.

## Current boundary

Repository/source implementation, registration, fail-closed tests, exact-head hosted validation, and merge are COMPLETE.

Issue #366 is complete for its repository-owned source deliverable. Authentic resident execution and proof consumption remain separately gated and are not implied by merge or hosted validation.
