# Reusable Task Ephemeral Construct Mirror Handoff

Updated: 2026-09-12

## Goal

Make every reusable task a durable identity whose invocation-specific parameters derive the exact manifest-bound RTG -> GTG -> TT construct and whose valid trigger automatically advances every declared machine-admissible internal step until completion or the first genuine authority, evidence, external-resource, human-decision, or unresolved-state boundary.

## Canonical source

- `data/reusable-task-registry.json`
- `data/reusable-task-ephemeral-construct-contract.json`
- `schemas/reusable-task-invocation-manifest.schema.json`
- `scripts/materialize_reusable_task_construct.py`
- `scripts/trigger_reusable_task.py`
- `scripts/run_ecosystem_continuity_reusable_task.py`
- `workers/reusable_task_lifecycle.py`
- `workers/reusable_task_master_records_roundtrip.py`
- `workers/finalize_reusable_task_entropy.py`
- `scripts/refresh_sovereign_worker_runtime_source.py`
- `data/task-coordination-policy.json`
- `management/COSV_PROFILE_V1.json`
- `StegVerse-Labs/StegScholar:papers/rtg-gtg-tt/cross-layer-contract.md`
- `master-records/orchestration:scripts/ingest_reusable_task_lifecycle.py`
- `master-records/orchestration:scripts/reconstruct_reusable_task_lifecycle.py`

## Durable / ephemeral invariant

```text
Reusable identity = durable
Parameters = invocation-specific
TT/RTG/GTG construct = derived
Trigger = single bounded invocation
Machine-admissible internal transitions = automatic
Runner = ephemeral where possible
Evidence = durable
Canonical task/COSV identity = durable when tracking is needed
Manifest = bound
Receipts = chained
Recording = at necessary levels
```

The cross-layer semantic order remains canonical `RTG -> GTG -> TT`. This repository does not redefine RTG, GTG, or TT mathematics or collapse their authority boundaries.

## Trigger-once automation invariant

A reusable task is not a checklist that requires the coordinator to manually re-drive each ordinary internal transition. After one valid trigger, `scripts/trigger_reusable_task.py` materializes the canonical invocation manifest and advances only the runner templates already declared by that reusable identity.

```text
valid reusable-task trigger
-> resolve durable identity + parameters
-> verify optional task_id/COSV binding
-> bind RTG/GTG/TT + automation + runner manifest
-> invoke the declared existing primary runner
-> retain its exact return boundary
-> if standardized manifest-bound completion evidence is absent: stop at evidence reconciliation
-> if standardized completion evidence is present: validate every declared completion predicate
-> observe runner process return / expiry
-> create non-executing residual recording construct
-> create source-only Master Records custody/reconstruction request
-> if existing local master-records/orchestration source is available:
     invoke destination-owned custody ingestion
     invoke destination-owned reconstruction
     require reconstructed request bytes == source request bytes
     validate returned destination custody record
     emit entropy-recovery receipt
-> otherwise stop at the exact Master Records runtime/source boundary
```

The automation driver does not create a scheduler, WorkerCoordinator, claim/fence path, credential route, InTr authority, provider authority, or Master Records authority. Exit code zero alone remains insufficient. Existing reusable runners that do not emit the standardized result continue to stop at `COMPLETION_PREDICATES_REQUIRE_EVIDENCE_RECONCILIATION`.

When a reusable identity has no executable runner declaration, the trigger is still recorded but stops at `NO_EXECUTABLE_RUNNER_DECLARED`. Independent downstream or parallel work may continue while a reusable task is at a boundary. Work that depends on its required completion evidence must wait for that evidence.

## Standardized runner evidence

`workers/reusable_task_lifecycle.py` recognizes `stegverse.reusable-task-runner-result/v1`. The result must bind the exact invocation ID, reusable-task ID, manifest hash, and the complete declared predicate set. It must state that runtime and completion evidence were observed and carry no authority effect.

The existing `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` identity is the first real ecosystem workload bound to this result shape. Its existing runner delegates to the Healer ECE cycle. A reusable result is written only when that cycle returns `state=COMPLETE`; blocked/failed cycles emit no standardized completion result.

That ECE cycle already performs SDK diagnostic processing, ECE evaluation, exact evaluation-byte custody/reconstruction through its existing Master Records path, Healer intake, and Site-safe projection. The reusable lifecycle binding does not replace any of those owners or reinterpret a failed cycle.

## Invocation lifecycle

```text
durable reusable identity
+ invocation parameters
+ task_id/COSV pointer when tracking is required
-> resolve existing canonical definition/equivalent work
-> derive RTG candidate envelope
-> derive GTG governance envelope
-> derive TT record/execution/observation envelope
-> bind invocation + automation manifest
-> trigger once
-> applicable WorkerCoordinator + Interlock/InTr admission
-> automatically advance declared bounded runner
-> exact runner result or exact governed boundary
-> runner expiry observation
-> residual non-executing recording construct
-> required scoped recording
-> source custody/reconstruction request
-> existing local master-records/orchestration destination ingestion
-> independent Master Records custody record
-> exact request-byte reconstruction
-> source verifies exact reconstructed bytes + destination record
-> entropy recovery
```

## Residual recording construct

After runner expiry, the remaining construct has no original execution purpose and no provider-operation, credential-acquisition, claim/fence, self-extension, or transition authority. It preserves invocation identity and manifest binding, carries the receipt chain and required recording levels, and remains until independent Master Records custody/reconstruction is returned.

## Master Records integration

The runtime destination is the already-required and already-local `master-records/orchestration` repository used by the ECE sandbox. No new Master Records runtime root is introduced.

The source request schema is `stegverse.reusable-task-master-records-custody-request/v1`. The source side leaves destination acceptance and acknowledgement false.

`workers/reusable_task_master_records_roundtrip.py` does not validate on behalf of Master Records and does not mint destination state. It resolves the already-local `master-records/orchestration` root from `STEGVERSE_REPO_ROOTS_JSON`, invokes the destination-owned ingest and reconstruction scripts, and verifies that reconstructed request bytes exactly equal the source request bytes before returning the destination record to the lifecycle verifier.

The destination scripts independently validate the exact manifest, trigger, runner-result, runner-expiry, residual-recording, hashes, completion predicates, recording coverage, and non-authority fields before retaining exact source bytes and emitting `master-records.reusable-task-lifecycle-custody/v1`.

Source request != destination custody acceptance. Matching hashes != truth. The `.github` lifecycle cannot self-mint the Master Records record.

The separately merged `master-records/core-lite` PR #39 remains a validated reference implementation of the same custody contract; it is not a new ECE runtime dependency.

## Entropy recovery

Entropy recovery is emitted only after:

- runner expiry;
- required recording-level coverage;
- exact source-request hash binding;
- exact evidence-bundle hash binding;
- destination custody acceptance;
- destination acknowledgement;
- independent validation;
- reconstruction confirmation;
- exact reconstructed request-byte equality; and
- absence of execution/runtime/publication authority escalation.

Entropy recovery displaces only the residual non-executing construct. It does not delete required evidence or Master Records history and does not reactivate the original runner.

## Resident propagation

The existing local-only WorkerCoordinator source refresher carries the reusable-task registry, construct contract, constructor, and trigger explicitly. The lifecycle closure, Master Records roundtrip adapter, and entropy finalizer live under `workers/`, which that same refresher already propagates recursively. No second source-distribution plane is introduced.

The ECE resident runtime already requires `master-records/orchestration` in its local repository-root map. Missing local source continues to fail closed; the lifecycle performs no GitHub/network fetch during resident execution.

## Authority boundaries

- Task Registry: work intent / coordination
- WorkerCoordinator: execution claim / fence
- Interlock/InTr: governed transitions
- TV/TVC: credential authority
- Master Records: observed reality / custody / reconstruction
- COSV: compact state projection
- Trigger driver: non-authorizing dependency orchestration
- GitHub token runtime authority: `NONE`

## Work completed

- PR #1690 merged the standardized manifest-bound runner result, runner expiry, residual recording, source custody request, entropy verifier/finalizer, and ECE reusable-result binding into `.github` at `46686bb4e83f2788cacc614594a875c175e0b78b` after Organization Control, Deterministic, and Heartbeat exact-head validation passed.
- `master-records/core-lite` PR #39 merged a separately validated reference implementation of independent lifecycle custody at `be0d08d73c96f50308991793327522dc01304657`.
- `master-records/orchestration` PR #93 merged the actual ECE-resident lifecycle ingest/reconstruction destination at `3507c5116ad9741f368bea0c563023f25729ac75`; its focused reusable lifecycle custody validation passed before merge.
- `.github` PR #1694 merged the resident Master Records roundtrip integration at `c35a12fdf1fa32b7890e923cf0889bb0ba570010` after exact-head Organization Control `34735304336`, Deterministic Repository Suite `34735304388`, and Heartbeat Worker Project `34735304350` all passed.
- The reusable trigger now advances from authentic standardized runner evidence through runner expiry, residual recording, destination-owned Master Records custody/reconstruction, exact reconstructed-request byte equality, and entropy recovery when the existing local runtime dependencies are present.
- Existing runners without standardized completion evidence still stop at evidence reconciliation; missing/rejected Master Records runtime source still stops at the exact destination boundary.
- The existing Healer reusable-task schedule already enables `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` hourly with bounded retries; no new scheduler was added.

## Work remaining to satisfy the goal

1. Observe one authentic post-merge `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` resident/sandbox invocation executed by the existing ecosystem scheduler.
2. Retain, from that same invocation, the manifest, trigger receipt, standardized runner result, runner-expiry receipt, residual-recording artifact, Master Records source request, destination custody record, exact reconstructed request bytes, and entropy-recovery receipt.
3. Verify that retained chain has no inferred, substituted, or cross-invocation links.

No additional source implementation is presently identified for this lifecycle. Quantitative performance/load assessment should be repeated only after the remaining runtime artifacts exist.
