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
- `workers/finalize_reusable_task_entropy.py`
- `scripts/refresh_sovereign_worker_runtime_source.py`
- `data/task-coordination-policy.json`
- `management/COSV_PROFILE_V1.json`
- `StegVerse-Labs/StegScholar:papers/rtg-gtg-tt/cross-layer-contract.md`

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
-> stop for independent destination custody/reconstruction
-> after an authentic Master Records destination record is returned, finalize entropy recovery
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
-> independent Master Records validation + destination record
-> entropy recovery
```

## Residual recording construct

After runner expiry, the remaining construct has no original execution purpose and no provider-operation, credential-acquisition, claim/fence, self-extension, or transition authority. It preserves invocation identity and manifest binding, carries the receipt chain and required recording levels, and remains until independent Master Records custody/reconstruction is returned.

## Master Records boundary

The source request schema is `stegverse.reusable-task-master-records-custody-request/v1`. The source side must leave destination acceptance and acknowledgement false.

The corresponding independent destination validator is developed in `master-records/core-lite` and returns `master-records.reusable-task-lifecycle-custody/v1` only after validating the exact manifest, trigger, runner-result, runner-expiry, residual-recording, hashes, completion predicates, recording coverage, and non-authority fields.

Source request != destination custody acceptance. Matching hashes != truth. The `.github` lifecycle cannot self-mint the Master Records record.

## Entropy recovery

`workers/finalize_reusable_task_entropy.py` accepts the independent Master Records destination record and emits entropy recovery only after verifying:

- runner expiry;
- required recording-level coverage;
- exact source-request hash binding;
- exact evidence-bundle hash binding;
- destination custody acceptance;
- destination acknowledgement;
- independent validation;
- reconstruction confirmation; and
- absence of execution/runtime/publication authority escalation.

Entropy recovery displaces only the residual non-executing construct. It does not delete required evidence or Master Records history and does not reactivate the original runner.

## Resident propagation

The existing local-only WorkerCoordinator source refresher carries the reusable-task registry, construct contract, constructor, and trigger explicitly. The lifecycle closure implementation and entropy finalizer live under `workers/`, which that same refresher already propagates recursively. No second source-distribution plane is introduced.

## Authority boundaries

- Task Registry: work intent / coordination
- WorkerCoordinator: execution claim / fence
- Interlock/InTr: governed transitions
- TV/TVC: credential authority
- Master Records: observed reality / custody / reconstruction
- COSV: compact state projection
- Trigger driver: non-authorizing dependency orchestration
- GitHub token runtime authority: `NONE`

## Work completed in the current source change

- Added standardized manifest-bound runner-result validation.
- Added runner process-return/expiry receipt construction.
- Added residual non-executing recording construction.
- Added source-only Master Records custody/reconstruction request construction.
- Added independent Master Records destination-record verification and entropy finalization.
- Bound the existing ECE reusable runner to emit the standardized result only after its real underlying ECE cycle returns `COMPLETE`.
- Preserved the previous evidence-reconciliation boundary for runners that do not emit standardized completion evidence.
- Kept lifecycle closure code on the already-propagated resident `workers/` source surface.

## Work remaining to satisfy the goal

1. Validate and merge the `.github` lifecycle closure source and the independent `master-records/core-lite` custody validator.
2. Have the ecosystem execute one authentic `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` invocation through its existing resident/sandbox path.
3. Retain the manifest, trigger, standardized runner result, runner-expiry receipt, and residual-recording artifact from that same invocation.
4. Deliver that invocation's exact source custody request to Master Records through the ecosystem's existing custody transport.
5. Observe the independently minted Master Records destination custody/reconstruction record for the same request/evidence hashes.
6. Feed that destination record to the resident entropy finalizer and retain the resulting entropy-recovery receipt.
7. Reconstruct the complete receipt chain without inferred links.

Until those remaining items are performed, the task still lacks the runtime information required for quantitative performance/load assessment.
