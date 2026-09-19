# SDK Evaluator Governance Posture Runtime Proof Mirror Handoff

Goal Task ID: `SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001`
Parent: `SDK-EVALUATOR-GOVERNANCE-POSTURE-MANIFEST-001`
COSV: `71000000100110`
Status: `ACTIVE / AUTHENTIC RUNTIME PROOF PENDING`

## Purpose
Own only the authentic resident execution proof transferred from the completed parent source/console goal. Reuse the existing resident dispatcher and exact SDK entry point `run_evaluator_governance_manifest`. Do not create another runtime, scheduler, governance/credential/transition authority, request path, or second user-operated device.

## Canonical execution path
```text
existing resident dispatcher
-> bounded sdk_evaluator_governance_posture consumer
-> exact manifested evaluator input
-> run_evaluator_governance_manifest
-> external_manifest_to_public_request
-> StegOS intr_security_posture_resolution.resolve_task_security_posture
-> Interlock/InTr posture resolution over exact task/payload/transition request
-> governed result
-> retained resident receipt
```

Registration/tests are source evidence only. Authentic completion requires a retained resident machine result binding exact manifest/graph hash when present, projected-input hash when applicable, transition_request_sha256, posture instance id/hash, `resolution_authority=INTERLOCK_INTR`, `posture_bound_execution=true`, `sdk_resolved_posture=false`, and custody/result locator. GitHub Actions cannot substitute.

TV/TVC remains credential authority; Interlock/InTr remains transition/posture authority; SDK is representation/transport/evidence only; HB is observability only; GitHub has no runtime authority. `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` remains a separate downstream consumer.

## First implementation seam
Add only the bounded request-specific consumer and dispatcher registration needed to invoke `run_evaluator_governance_manifest` from the existing resident carrier. Reuse WorkerCoordinator/ProcessWorkerAdapter/Interlock paths where admission is required; do not repurpose READ_REVIEW or create a parallel runtime.

## Source consumer implementation — 2026-09-18

The bounded resident seam is implemented in source using only the existing dispatcher: `sdk_evaluator_governance_posture` -> `scripts/consume_sdk_evaluator_governance_posture_request.py`, with request `control/resident-execution-request.d/sdk-evaluator-governance-posture-runtime-proof-001.json`. The consumer requires an already-materialized exact manifest, records its byte SHA-256, invokes only `stegverse.evaluator_governance_runtime.run_evaluator_governance_manifest`, and retains the returned Interlock/InTr posture binding under `receipts/sovereign-host/sdk-evaluator-governance-posture-runtime-proof.latest.json`. Source refresh/materialization carries the consumer. CI validation remains non-authorizing and cannot satisfy the authentic retained runtime predicate.

## Canonical runtime-model reconciliation — 2026-09-18

The Task Registry runtime contracts were re-read before continuing this Goal. The governing interpretation is:

- `data/task-registry-global-invariants.json` applies to this task: Remote Computer inventory is evidence-reachability only, zero connected devices is not a runtime blocker, StegOS execution nodes are interchangeable, and runtime-capable tasks must evaluate the canonical single-device-first substrate order.
- `docs/REMOTE_RUNTIME_CONNECTOR_OPTIONALITY.md` explicitly states that event-ephemeral runtime may materialize without a remote connector and that zero connected devices neither proves runtime unavailability nor creates a second-machine requirement.
- `docs/HB32_RUNTIME_SOLUTION_REUSE_MIRROR_HANDOFF.md` requires reuse of the existing carrier/self-heal/source-refresh/dispatcher stack and prohibits treating a missing runtime signal as justification for a new runtime.
- `docs/GLOBAL_RUNTIME_EVIDENCE_CLOSURE_MIRROR_HANDOFF.md` and the convergence matrix establish the shared runtime-evidence model and canonical substrate review order. This task owns only its subject-bound SDK posture execution predicate; it does not own runtime materialization infrastructure.
- `control/canonical-resident-carrier-contract.json` preserves one WorkerCoordinator/dispatcher and prohibits a second resident runtime or scheduler.

Therefore the prior observation that a Remote Computer connector exposed zero devices is not a blocker and must not be used to decide whether this task can progress. The task-local first unresolved predicate is instead `EXACT_EVALUATOR_MANIFEST_MATERIALIZED_ON_ADMITTED_CANONICAL_RUNTIME_SUBSTRATE`.

The manifest's canonical source owner already exists in `StegVerse-org/StegVerse-SDK`: the parent evaluator-governance-posture manifest builder/source contract. No second manifest builder is authorized here. The resident request's `runtime-state/sdk-evaluator-governance-posture/manifest.json` is the runtime locator, not proof that the manifest has already been materialized. After exact SDK manifest materialization on the first eligible admitted canonical substrate, the already-merged `sdk_evaluator_governance_posture` selector remains the only task-specific resident dispatch path. Its retained result must then pass exact hash/posture bindings and Master Records custody/reconstruction before this Goal can promote runtime evidence.

## Master Records success/failure authority binding — 2026-09-18

Master Records is the canonical source used to determine success/failure boundaries for every resulting governed state transition in this Goal. Repository/search absence is not itself runtime failure. The task-specific consumer now routes its resulting `COMPLETED` or `ATTEMPT_RECORDED` transition through the already-existing `workers/canonical_state_transition_custody.py` seam and declares the exact retained SDK runtime receipt as required evidence. Promotion to task-level `COMPLETED` requires the authoritative Master Records return to be `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, and `receipt_sha256 == reconstructed_receipt_sha256`. Any absent/unavailable/failing Master Records return remains non-terminal and exposes that exact custody boundary; it is not converted into a runtime/substrate inference. Interlock/InTr remains transition authority and Master Records grants no transition or execution authority.

## RESIDENT_REQUEST_DISPATCH_VISIT Master Records carriage repair — 2026-09-18

Current canonical state was re-read before mutation. Master Records still contained no authentic `RESIDENT_REQUEST_DISPATCH_VISIT` transition for `sdk_evaluator_governance_posture`. The concrete source carriage defect remained: `scripts/dispatch_resident_execution_requests.py` retained the selector visit and machine result locally but did not submit that exact dispatch transition through canonical state-transition custody.

The existing dispatcher now retains only an attempted `sdk_evaluator_governance_posture` visit through `workers/canonical_state_transition_custody.py`. Its required evidence follows the current six-field Master Records contract and binds selector, consumer ref, attempted=true, exact task/request identity, machine-result digest, and machine result. Consumer selection, invocation order, execution, and dispatcher authority are unchanged. Authentic progression remains prohibited unless Master Records returns `RECORDED + reconstruction_status=PASS + required_evidence_validation_status=PASS` with exact receipt/reconstruction digest equality. This source repair does not claim runtime execution.

## Recovered pre-drift manifest-materialization boundary — 2026-09-19

The current Task Registry/runtime contracts and Master Records custody semantics were re-read before continuing. The task's legitimate first local unresolved predicate remains `EXACT_EVALUATOR_MANIFEST_MATERIALIZED_ON_ADMITTED_CANONICAL_RUNTIME_SUBSTRATE`. `RESIDENT_REQUEST_DISPATCH_VISIT` is not used as the predecessor for this continuation. Repository-visible Master Records reconstruction for this exact task/request was not surfaced; under `MISSING_EVIDENCE_IS_NOT_PROOF_OF_NON_OCCURRENCE`, that is an unverified evidence surface, not a non-occurrence claim.

Tracing the exact recovered boundary exposed a deterministic source-path defect independent of any absence inference: the resident request declared `runtime-state/sdk-evaluator-governance-posture/manifest.json`, and the existing consumer refused execution when that file was absent, but the resident source-refresh/bootstrap path contained no production materialization step for that locator. Tests had been creating the file manually.

The existing path now repairs only that seam. The same resident request declares the exact committed SDK source inputs and the already-canonical `stegverse.evaluator_manifest_builder.build_evaluator_governance_manifest` builder. When the runtime locator is absent, the existing consumer uses the already-local `STEGVERSE_SDK_SOURCE_ROOT` to build the manifest, binds `security_posture_request.task_id` to this Goal Task ID, writes the exact runtime locator atomically, records input-file SHA-256 bindings, and then continues through the existing `run_evaluator_governance_manifest` path. Materialization has authority effect `NONE_INPUT_MATERIALIZATION_ONLY`.

This is source-path repair, not runtime proof. It does not establish which eligible canonical substrate performed the materialization, does not claim an authentic WorkerCoordinator claim/fence or Interlock/InTr transition, and does not promote Master Records reconstruction. The next authentic evidence must come from the existing admitted runtime path and be reconciled through Master Records without inferring non-occurrence from an unsurfaced record.
