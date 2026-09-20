# SDK TT Purpose-Bound Worker Test 1 Authentic Runtime Mirror Handoff

Updated: 2026-09-20
Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-TEST1-AUTHENTIC-RUNTIME-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `71000000111111`
Status: ACTIVE / UNCLAIMED
Canonical Task Registry generation: 139

## Purpose

Close Evaluator Test 1 through the already-existing universal Manifest Builder -> run-manifest -> shared Universal InTr -> WorkerCoordinator -> TV/TVC -> Interlock/InTr -> StegAgents -> Master Records path. This successor observes and closes the original execution lineage; it does not create a new runtime task identity, listener, scheduler, dispatcher, WorkerCoordinator, credential path, custody store, repository subprocess bridge, test-specific execution lane, or device dependency.

## Inherited source closure

- Shared Universal InTr profile: .github PR #2341, merge `746d077e126e3452ccb40685907f141c839fb851`; validation run `35526393070` SUCCESS.
- SDK universal runtime and Test-1-only validation: SDK PR #288, merge `ec989d1e2075b975c7cc138ceec4ee0fabdd1d50`; Test 1 run `35527445140` SUCCESS; package run `35527445139` SUCCESS.
- Test 1 CI first boundary: `UNIVERSAL_INTR_INGRESS_NOT_CONFIGURED`, exit 2. This is GitHub non-runtime boundary evidence, not a resident runtime failure.
- Canonical resident endpoint binding: `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL`.
- Canonical existing TVC transport authorization binding: `STEGVERSE_TVC_RELAY_AUTHORIZATION_ID`.
- Request grants no authority. WorkerCoordinator remains claim/fence authority; TV/TVC remains credential/warrant authority; Interlock/InTr remains transition authority; StegAgents remains domain execution; Master Records remains custody/replay/reconstruction authority.

## Required exact execution lineage

The execution target remains `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` because the manifest/state graph is already bound to that canonical task lineage. The successor task coordinates and verifies closure only.

```text
Manifest Builder -> run-manifest
-> shared /intr/materialization SDK:ManifestStateTransition
-> WORKERCOORDINATOR_CLAIM_FENCE_BOUND
-> Master Records closure
-> TV_TVC_WARRANT_POLICY_VERIFIED
-> Master Records closure
-> STEGCORE_INTR_MATERIALIZATION_ADMITTED
-> Master Records closure
-> PURPOSE_BOUND_WORKER_MATERIALIZED
-> Master Records closure
-> PURPOSE_BOUND_WORKER_INVOCATION_STARTED
-> Master Records closure
-> PURPOSE_BOUND_WORKER_TASK_COMPLETED
-> Master Records closure
-> PURPOSE_BOUND_WORKER_RETIRED
-> Master Records closure
-> replay PASS + reconstruction PASS
-> records_only=true + continued_authority=false
-> exact manifest_receipt_id bound to original manifest lineage
```

Every successor transition requires the immediately preceding Master Records closure with `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and exact `receipt_sha256 == reconstructed_receipt_sha256`.

## Execution rule

Run Test 1 only. Do not advance to Test 2 or Test 3 until authentic Test 1 completion closes end to end. If the resident execution returns a concrete failure, retain the exact first failure and repair only that same existing canonical path. Absence of a GitHub resident endpoint is not a runtime defect and must not be repaired by adding GitHub runtime authority.

## Authentic runtime observation — 2026-09-20

Canonical generation 140 was re-read after the parent retirement/successor registration merged. The parent coordination record is RETIRED, while the preserved execution lineage remains independently executable: `control/worker-registry.d/sdk-tt-purpose-bound-worker-runtime-proof-001.json` is still `HANDOFF_READY` with `claim_state=AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM`, and the exact resident request `RESIDENT-EXEC-SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` remains staged.

The shared SDK ingress is the existing `SDK:ManifestStateTransition` profile at `/intr/materialization`. Resident Universal InTr is intentionally loopback-only; no public endpoint or GitHub Actions path may substitute. The available authorized remote-control connector reported zero connected devices, and repository evidence still contains no retained authentic Test 1 purpose-runtime receipt. This is recorded only as a control-surface observation, not as a StegVerse device prerequisite or runtime failure.

No source defect was identified in the Test 1 chain, no Test 2/3 execution occurred, and no substitute invocation was issued. The exact next authentic transition remains `AUTHENTIC_TEST1_UNIVERSAL_INTR_INGRESS_CONSUMPTION`, after which the existing WorkerCoordinator -> TV/TVC -> Interlock/InTr -> StegAgents -> Master Records sequence must close state-dependently.

## Test 1 regression diagnosis and repair — 2026-09-20

The prior resident-Universal-InTr requirement for Evaluator Test 1 was traced to a regression, not to the original Test 1 contract.

Last known good behavior was SDK merge `a3a2039f907fe6499f32b79c7112c6be9495f5a4`: Manifest Builder produced the manifest, `run-manifest` selected `purpose_bound_worker_processor.execute_manifest`, that processor called the installed `run_purpose_bound_worker`, and the returned result contained the complete Test 1 lifecycle `MATERIALIZED -> INVOCATION_STARTED -> TASK_COMPLETED -> RETIRED` with `records_only=true` and `worker_live_after_close=false`.

SDK PR #285 was the first behavior-breaking change. It deliberately classified that working result as a false semantic PASS and changed public `run-manifest` to fail with `AUTHENTIC_GOVERNED_RUNTIME_BINDING_REQUIRED`. PR #286 then rebound the purpose-bound route to `manifest_state_transition_runtime.execute_manifest`, making an external `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL` mandatory. Those changes caused the observed Test 1 regression.

SDK PR #289 restored Test 1 only to the working manifest-selected processor path while leaving the newer generic universal runtime code available for other work. Exact-head Test 1 run `35534933752` passed and required the assembled lifecycle result; SDK package run `35534933786` also passed. PR #289 merged as `3948fbcb7fd4deb185bf6eb815b3410f8abf6fee`.

Canonical Test 1 success is therefore again: manifest is the only variable input -> Manifest Builder -> `run-manifest` -> installed purpose-bound processor -> assembled lifecycle result. An external resident Universal InTr endpoint is not a Test 1 success criterion. Tests 2 and 3 were not executed by this repair.

