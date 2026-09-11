# GADI Resident Execution Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `SOURCE_RESOLUTION_MERGED_VALIDATED / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and is not superseded. Canonical runtime-evidence materialization was already merged at `2a86ea27ce222eda7f248e448e17d084004b7ede`.

PR `StegVerse-Labs/.github#1341` was validated at exact head `e56cef0c93345654f8cd393a10bc7f3b9280e171` with all observed checks successful and then squash-merged as `5b5d795d89b75829c4101719dc8c9f75c227c2d7`.

That merge adds local-only authentic runtime source resolution and changes the GADI execution chain to:

```text
SOURCE RESOLUTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
```

The resolver never performs network fetches, never mints authority, rejects unsafe or escaping source paths, validates JSON, copies exact bytes into canonical staging paths, and records SHA-256 bindings. Existing authentic staged sources remain supported when no locator manifest is present.

## Purpose

This task installs and executes the canonical WorkerCoordinator/resident-request seam for authentic GADI defensive execution. It does not create a new runtime, scheduler, claim/fence plane, InTr authority, provider transport, credential route, or actuator.

The authentic execution chain is:

```text
current GADI command already admitted by InTr
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
- `tests/test_gadi_resident_execution_preflight.py`
- `tests/test_gadi_resident_execution_request.py`

Merged downstream implementation reused:

`StegVerse-002/micro-node-runtime/micro_node/gadi_resident_consumer.py`

## Authentic source inputs

The source resolver accepts either already-staged authentic files or a local-only locator manifest at:

`state/gadi-resident-execution/source-locators.json`

The four authentic source classes are:

```text
StegOS command
current InTr admission
current WorkerCoordinator claim/fence
controlled pre-authorized actuator observation
```

Canonical staging paths are:

```text
state/gadi-resident-execution/source/stegos-command.json
state/gadi-resident-execution/source/intr-admission.json
state/gadi-resident-execution/source/worker-claim.json
state/gadi-resident-execution/source/actuator-observation.json
```

Successful materialization projects the validated current evidence into the exact resident-consumer paths:

```text
state/gadi-resident-execution/command.json
state/gadi-resident-execution/execution-context.json
state/gadi-resident-execution/actuator-result.json
```

## Evidence boundary

Source implementation, GitHub validation, merge state, request registration, source resolution, and materialization source code are not resident execution evidence.

A successful resident execution claim requires authentic current runtime-local inputs from the existing StegOS/InTr/WorkerCoordinator/actuator planes, exact binding across those inputs, successful preflight, actual resident consumption, and a resulting subject-bound receipt.

Output:

`receipts/sovereign-host/gadi-resident-execution-consumption.latest.json`

A qualifying receipt must preserve exact claim/fence, InTr decision, runtime binding, subject, control surface, target, observed state, effect, reassessment, and stop-condition fields while explicitly recording that no execution authority, scheduler/runtime, or Master Records reconciliation was created by the request/materialization tooling.

## Remaining authentic completion predicates

1. Produce or locate an authentic current StegOS GADI command for parent `GADI-001`.
2. Produce or locate the exact current InTr admission for that command and runtime binding.
3. Obtain the current WorkerCoordinator claim/fence for `GADI-RESIDENT-EXECUTION-001`.
4. Produce a controlled pre-authorized actuator observation bound to the same runtime/control surface/target/subject.
5. Run source resolution -> materialization -> preflight -> resident consumption against those exact local bytes.
6. Emit and independently inspect the subject-bound resident consumption receipt.
7. Complete GADI closed-loop reassessment/adaptation/termination evidence.
8. Pass the authentic receipt chain to Continuity/Master Records and prove exact reconstruction.
9. Reconcile parent `GADI-001` and the umbrella manifold only from those authentic observations.

## Immediate continuation

Do not synthesize any of the four source classes in CI or GitHub. The next runtime-capable continuation should inspect the active local resident runtime for the authentic StegOS command, InTr decision, WorkerCoordinator claim/fence, and actuator observation; write only local locator references or reuse already-staged exact bytes; then invoke the merged dispatcher.

If one or more source classes do not yet exist, the correct remediation is to repair the corresponding existing producer/authority plane rather than fabricate an input or add a second runtime plane.

## Collision boundary

No second heartbeat, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

README reviewed after PR #1341. The repository already documents the generic canonical resident-request -> WorkerCoordinator execution pattern and its authority separation. The source-locator merge remains an implementation refinement of that documented contract, so no additional top-level README wording is required at this point.

## Release rule

This source slice is not a GADI release or activation. Release/tag propagation remains deferred until the parent GADI task satisfies authentic resident runtime execution, closed-loop evidence, reconstruction, and canonical activation predicates.
