# GADI Resident Execution Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `SOURCE_RESOLUTION_MERGED_VALIDATED / STEGOS_COMMAND_CONTRACT_REPAIR_MERGED / INTR_ADMISSION_CONTRACT_REPAIR_IN_VALIDATION / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and is not superseded.

Canonical runtime-evidence materialization was merged at `2a86ea27ce222eda7f248e448e17d084004b7ede`.

PR `StegVerse-Labs/.github#1341` validated local-only authentic runtime source resolution and the four-stage chain and merged as `5b5d795d89b75829c4101719dc8c9f75c227c2d7`:

```text
SOURCE RESOLUTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
```

PR `StegVerse-Labs/.github#1351` reconciled this handoff and merged as `04150ebcfc58c275afefb069792461176960b7c8` after exact-head validation.

PR `StegVerse-Labs/.github#1362` repaired the native StegOS command producer/consumer mismatch. Exact head `4eddc1b5446284e24eec36699b8b80ae002f08cc` passed GADI preflight validation, organization-control validation, deterministic repository diagnostics, and Heartbeat validation, then squash-merged as `aad9915f6bfbe48bb75ce78d23e101ed0c3f7ff0`.

The bridge now correctly accepts authentic native StegOS consequential commands with:

```text
task_id = GADI-001
command_state = READY_FOR_RESIDENT_EXECUTION
```

while retaining fail-closed compatibility for prior bridge projections.

## InTr admission contract repair now in validation

Inspection of canonical GADI contracts found the next authority-boundary mismatch.

Canonical GADI admission is represented as:

```json
{
  "admission": {
    "state": "ADMITTED",
    "intr_decision_ref": "..."
  }
}
```

The canonical `Admission` model requires an InTr decision reference for `ADMITTED` state but does not contain or own `runtime_binding_ref`. Runtime binding is introduced later by the native StegOS command/runtime execution binding.

The resident materializer was incorrectly requiring `runtime_binding_ref` on the separate `intr-admission.json` source and comparing that value to the StegOS command. That requirement crossed authority boundaries and would reject an authentic canonical GADI admission artifact.

Current repair branch:

`gadi-intr-admission-contract-repair-001`

The repair:

1. recognizes authentic nested `admission.state` and `admission.intr_decision_ref` from canonical GADI intervention-request artifacts;
2. retains top-level admission projection compatibility for existing local evidence without promoting it over the canonical form;
3. removes the false requirement that InTr admission itself own a runtime binding;
4. continues to require exact `intr_decision_ref` equality between the authentic InTr admission and native StegOS command;
5. continues to require exact runtime-binding equality between the StegOS command and WorkerCoordinator execution context;
6. records the exact InTr source SHA-256 in the materialized execution context;
7. adds regressions proving canonical nested admission succeeds without an InTr runtime-binding field, mismatched InTr decisions fail closed, and command/claim runtime-binding mismatch still fails closed.

No InTr decision, runtime binding, claim/fence, actuator observation, command value, credential, or execution authority is synthesized.

## Purpose

This task installs and executes the canonical WorkerCoordinator/resident-request seam for authentic GADI defensive execution. It does not create a new runtime, scheduler, claim/fence plane, InTr authority, provider transport, credential route, or actuator.

The authentic execution chain is:

```text
current native StegOS GADI command already admitted by InTr
+ exact authentic InTr admission decision
+ current WorkerCoordinator claim/fence context
+ exact current runtime binding
+ controlled pre-authorized actuator result
+ merged micro-node GADI resident consumer
-> subject-bound resident consumption receipt
-> later Continuity/Master Records reconstruction
```

## Canonical surfaces

- `data/canonical-task-records/GADI-001.json`
- `data/canonical-task-records/GADI-RESIDENT-EXECUTION-001.json`
- `handoffs/GADI-RESIDENT-EXECUTION-001.json`
- `control/task-vectors/GADI-RESIDENT-EXECUTION-001.json`
- `control/task-vector-index.d/GADI-RESIDENT-EXECUTION-001.json`
- `control/resident-execution-request.d/gadi-resident-execution-001.json`
- `control/resident-execution-request.d/consume-gadi-resident-execution.py`
- `control/worker-registry.d/gadi-resident-execution-001.json`
- `control/process-worker-adapters.d/gadi-resident-execution-001.json`
- `scripts/resolve_gadi_resident_runtime_sources.py`
- `scripts/materialize_gadi_resident_runtime_bundle.py`
- `scripts/preflight_gadi_resident_execution.py`
- `scripts/dispatch_gadi_resident_execution.py`
- `tests/test_gadi_runtime_source_resolution.py`
- `tests/test_gadi_runtime_evidence_materializer.py`
- `tests/test_gadi_stegos_command_contract.py`
- `tests/test_gadi_stegos_preflight_contract.py`
- `tests/test_gadi_resident_execution_preflight.py`
- `tests/test_gadi_resident_execution_request.py`

Merged downstream implementation reused:

`StegVerse-002/micro-node-runtime/micro_node/gadi_resident_consumer.py`

## Authentic source inputs

The source resolver accepts either already-staged authentic files or a local-only locator manifest at:

`state/gadi-resident-execution/source-locators.json`

The four authentic source classes remain:

```text
StegOS command
current InTr admission
current WorkerCoordinator claim/fence
controlled pre-authorized actuator observation
```

Canonical staging paths:

```text
state/gadi-resident-execution/source/stegos-command.json
state/gadi-resident-execution/source/intr-admission.json
state/gadi-resident-execution/source/worker-claim.json
state/gadi-resident-execution/source/actuator-observation.json
```

Successful materialization projects validated current evidence into:

```text
state/gadi-resident-execution/command.json
state/gadi-resident-execution/execution-context.json
state/gadi-resident-execution/actuator-result.json
```

## WorkerCoordinator producer state

The canonical registered GADI worker exists and remains `HANDOFF_READY`, but current repository registration still has no authentic `claim_id`, worker instance, assignment timing, or fencing token. Therefore WorkerCoordinator execution evidence is not yet claimed.

The existing WorkerCoordinator assignment machinery already owns `claim_id`, `worker_instance_id`, and `fencing_token`. The runtime continuation must obtain those values from that existing plane rather than minting them in the GADI bridge.

## Evidence boundary

Source implementation, GitHub validation, merge state, request registration, source resolution, materialization, and preflight code are not resident execution evidence.

A successful resident execution claim requires authentic current runtime-local inputs from the existing StegOS/InTr/WorkerCoordinator/actuator planes, exact cross-surface binding, successful preflight, actual resident consumption, and a subject-bound receipt.

Output:

`receipts/sovereign-host/gadi-resident-execution-consumption.latest.json`

A qualifying receipt must preserve exact claim/fence, InTr decision, runtime binding, subject, control surface, target, observed state, effect, reassessment, and stop-condition fields while explicitly recording that request/materialization tooling minted no execution authority and created no scheduler/runtime or Master Records reconciliation.

## Remaining authentic completion predicates

1. Validate and merge the InTr admission contract repair without weakening fail-closed decision binding.
2. Produce or locate an authentic current native StegOS GADI command for `GADI-001`.
3. Produce or locate the exact current canonical InTr admission carrying the matching `intr_decision_ref`.
4. Obtain the current WorkerCoordinator claim/fence for `GADI-RESIDENT-EXECUTION-001` from the existing WorkerCoordinator authority plane.
5. Produce a controlled pre-authorized actuator observation bound to the same runtime/control surface/target/subject.
6. Run source resolution -> materialization -> preflight -> resident consumption against those exact local bytes.
7. Emit and independently inspect the subject-bound resident consumption receipt.
8. Complete GADI closed-loop reassessment/adaptation/termination evidence.
9. Pass the authentic receipt chain to Continuity/Master Records and prove exact reconstruction.
10. Reconcile parent `GADI-001` and the umbrella manifold only from those authentic observations.

## Immediate continuation

After this InTr repair validates and merges, inspect the WorkerCoordinator claim/fence producer and projection path for direct compatibility with `worker-claim.json`, then inspect the controlled pre-authorized actuator-observation producer.

Do not synthesize any authentic source class in CI or GitHub. If a source class is absent, repair the corresponding existing producer/authority plane rather than fabricate evidence or create a second runtime plane.

## Collision boundary

No second heartbeat, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

`README.md` was reviewed for this repair. Existing documentation already states the generic canonical resident-request/WorkerCoordinator authority separation, Universal InTr non-authorizing transport semantics, and local-only source-refresh model. This slice corrects an internal evidence-authority boundary and does not introduce a new top-level interface, so no README text mutation is required.

## Release rule

This source slice is not a GADI release or activation. Release/tag propagation remains deferred until authentic resident runtime execution, closed-loop evidence, reconstruction, and canonical activation predicates are satisfied.
