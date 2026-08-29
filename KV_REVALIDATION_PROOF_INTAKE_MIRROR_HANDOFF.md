# KV Revalidation Proof Intake Mirror Handoff

Status: SOURCE_MERGED_VALIDATED / RESIDENT_EXECUTION_PENDING
Repository: `StegVerse-Labs/.github`
Issue: #424
Branch: `feature/kv-revalidation-proof-intake-424`
Updated: 2026-08-29
Authority effect: NONE
Credential authority: TV/TVC
Production execution authority: SOVEREIGN_RESIDENT_ONLY

## Purpose

Close the machine-input gap between separately governed, already-produced non-secret connection revalidation proofs and the merged `KV-CONNECTION-REVALIDATION-WORKER-001` resident worker.

The bridge is an intake/dispatch mechanism only. It does not produce provider conformance, perform provider login, resolve SKAP material, prove private-KV readback, or restore `VERIFIED` itself.

## Canonical flow

```text
bounded local intake manifest
 -> fail-closed resident intake validation
 -> exact local proof/file bindings
 -> existing KV-CONNECTION-REVALIDATION-WORKER-001
 -> canonical CVK proof admission
 -> private-KV persistence when authentic proofs pass
```

## Hard boundaries

1. GitHub/hosted surfaces may validate source only and must fail closed for production intake.
2. Input manifest and referenced proof objects are local non-secret files only; URL/network locators are prohibited.
3. Credential-like manifest keys and credential-bearing environment are prohibited.
4. The bridge may invoke only the existing `KV-CONNECTION-REVALIDATION-WORKER-001` source path.
5. The bridge may not synthesize, alter, upgrade, or infer either proof object.
6. The bridge may not claim provider/session success, readback success, connection verification, or live activation.
7. Provider operation authority remains NONE; credential authority remains TV/TVC.
8. A dispatch receipt proves only admitted local intake and bounded invocation, not downstream success.

## Required source

- `KV_REVALIDATION_PROOF_INTAKE_MIRROR_HANDOFF.md`
- `schemas/kv-revalidation-proof-intake.schema.json`
- `workers/kv_revalidation_proof_intake_worker.py`
- `tests/test_kv_revalidation_proof_intake_worker.py`
- `scripts/check_kv_revalidation_proof_intake.py`
- executable handoff, worker-registry fragment, process adapter, and bounded cost basis

## Completion predicates

Repository/source completion requires deterministic proof that the intake bridge:

- rejects hosted and credential-bearing execution;
- rejects URL/network and missing local proof paths;
- rejects credential-like or authority-expanding manifest fields;
- binds one exact assembly and the exact existing revalidation task;
- forwards only the bounded non-secret runtime bindings required by the existing worker;
- emits a non-secret dispatch receipt without asserting revalidation success;
- preserves provider-operation authority NONE and TV/TVC credential authority;
- is registered as a separately fenced independent task-control worker;
- passes exact-head validation before merge.

## Runtime completion boundary

Source completion is not connection activation. Authentic runtime completion still requires a sovereign/resident runtime, separately produced conformance and readback proofs, canonical proof admission, and inspectable private-KV VERIFIED/health-receipt persistence from the existing revalidation worker.

## Current implementation state

The complete repository source surface is installed on `feature/kv-revalidation-proof-intake-424`, including the intake schema, worker, deterministic worker tests, executable handoff, worker registry, process adapter, bounded cost basis, Admissible-Existence projection, task.v1 COSV record, global index/coverage projection, COSV parity tests, and static boundary checker.

Current canonical task vector: `50000000102000`.

Worker denominator after this separately registered task: 58 total worker task IDs, 36 canonically indexed, 15 active-unvectorized, 6 completed historical, and 1 superseded historical.

Exact-head validation passed on `461258e1ad3d97cbee876c3676c0b28e62151406`:
- organization-control run `33274163163`: SUCCESS;
- Heartbeat Worker run `33274163282`: SUCCESS.

PR #426 merged as `673bda3e85a7e6f8f4de1a9f1e2309a92938fa33`.

The repository/source goal is complete. No live intake, provider proof, readback proof, connection verification, or runtime activation is claimed by source completion.
