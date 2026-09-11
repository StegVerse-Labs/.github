# GADI Resident Execution Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `SOURCE_RESOLUTION_MERGED_VALIDATED / STEGOS_COMMAND_CONTRACT_REPAIR_IN_VALIDATION / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and is not superseded.

Canonical runtime-evidence materialization was merged at `2a86ea27ce222eda7f248e448e17d084004b7ede`.

PR `StegVerse-Labs/.github#1341` was validated at exact head `e56cef0c93345654f8cd393a10bc7f3b9280e171` and squash-merged as `5b5d795d89b75829c4101719dc8c9f75c227c2d7`, adding local-only authentic runtime source resolution and the four-stage chain:

```text
SOURCE RESOLUTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
```

PR `StegVerse-Labs/.github#1351` was then validated at exact head `2309284a14d8e3a2a04affc8cd3ea121f5891973` with all three observed validation workflows successful and squash-merged as `04150ebcfc58c275afefb069792461176960b7c8`, reconciling this handoff to that merged source-resolution state.

## Producer-contract repair now in validation

Inspection of the authentic StegOS producer found a real integration mismatch.

The merged native StegOS GADI producer at `StegVerse-Labs/StegOS/stegos/gadi_native_defense.py` emits consequential commands with:

```text
task_id = GADI-001
command_state = READY_FOR_RESIDENT_EXECUTION
```

The `.github` resident materializer and preflight were instead validating:

```text
task_id = GADI-RESIDENT-EXECUTION-001
state = READY_FOR_RESIDENT_EXECUTION
```

That meant an authentic native StegOS command could be rejected before resident consumption even when its InTr/runtime bindings were correct.

Current repair branch:

`gadi-stegos-command-contract-repair-001`

The repair:

1. makes `scripts/materialize_gadi_resident_runtime_bundle.py` accept the parent `GADI-001` native command identity while still permitting the existing child-compatible form;
2. makes materialization recognize native `command_state`, with legacy `state` retained only as compatibility fallback;
3. makes `scripts/preflight_gadi_resident_execution.py` use the same native `command_state` semantics;
4. adds `tests/test_gadi_stegos_command_contract.py` to prove the authentic StegOS producer shape reaches materialization successfully and unrelated task identities still fail closed;
5. adds `tests/test_gadi_stegos_preflight_contract.py` to prove the native StegOS `command_state` survives through preflight to `READY_FOR_RESIDENT_CONSUMPTION`.

No command values, authority, claims, fences, InTr decisions, runtime bindings, or actuator results are synthesized by this repair.

## Purpose

This task installs and executes the canonical WorkerCoordinator/resident-request seam for authentic GADI defensive execution. It does not create a new runtime, scheduler, claim/fence plane, InTr authority, provider transport, credential route, or actuator.

The authentic execution chain is:

```text
current native StegOS GADI command already admitted by InTr
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

The downstream micro-node tests already use the authentic native StegOS `command_state` field, so the current repair aligns the `.github` bridge to the already-merged producer/consumer contract rather than changing the downstream consumer contract.

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

Successful materialization projects the validated current evidence into:

```text
state/gadi-resident-execution/command.json
state/gadi-resident-execution/execution-context.json
state/gadi-resident-execution/actuator-result.json
```

## WorkerCoordinator producer state

The canonical registered GADI worker exists and remains `HANDOFF_READY`, but the current repository worker fragment still has null `claim_id`, null worker instance, null heartbeat timing, and no fence. The task therefore must not claim WorkerCoordinator execution evidence yet.

The existing WorkerCoordinator assignment machinery already defines the authoritative `claim_id`, `worker_instance_id`, and `fencing_token` custody model. The next runtime-capable step is to obtain the authentic current claim/fence from that existing plane, not to mint one in the GADI bridge.

## Evidence boundary

Source implementation, GitHub validation, merge state, request registration, source resolution, materialization, and preflight source code are not resident execution evidence.

A successful resident execution claim requires authentic current runtime-local inputs from the existing StegOS/InTr/WorkerCoordinator/actuator planes, exact binding across those inputs, successful preflight, actual resident consumption, and a resulting subject-bound receipt.

Output:

`receipts/sovereign-host/gadi-resident-execution-consumption.latest.json`

A qualifying receipt must preserve exact claim/fence, InTr decision, runtime binding, subject, control surface, target, observed state, effect, reassessment, and stop-condition fields while explicitly recording that no execution authority, scheduler/runtime, or Master Records reconciliation was created by request/materialization tooling.

## Remaining authentic completion predicates

1. Validate and merge the StegOS command-contract repair without weakening fail-closed behavior.
2. Produce or locate an authentic current native StegOS GADI command for parent `GADI-001`.
3. Produce or locate the exact current InTr admission for that command and runtime binding.
4. Obtain the current WorkerCoordinator claim/fence for `GADI-RESIDENT-EXECUTION-001` from the existing WorkerCoordinator authority plane.
5. Produce a controlled pre-authorized actuator observation bound to the same runtime/control surface/target/subject.
6. Run source resolution -> materialization -> preflight -> resident consumption against those exact local bytes.
7. Emit and independently inspect the subject-bound resident consumption receipt.
8. Complete GADI closed-loop reassessment/adaptation/termination evidence.
9. Pass the authentic receipt chain to Continuity/Master Records and prove exact reconstruction.
10. Reconcile parent `GADI-001` and the umbrella manifold only from those authentic observations.

## Immediate continuation

After the current contract repair validates and merges, inspect the native InTr admission producer shape against `intr-admission.json` requirements and repair any producer/consumer mismatch found there. Then inspect WorkerCoordinator claim/fence projection and the controlled pre-authorized actuator observation producer.

Do not synthesize any of the four source classes in CI or GitHub. If a source class does not exist authentically, repair its existing producer/authority plane rather than fabricating the input or creating a second runtime plane.

## Collision boundary

No second heartbeat, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

`README.md` was reviewed for this repair. The repository already documents the generic canonical resident-request -> WorkerCoordinator authority separation and local-only source-refresh model. This change fixes an internal field/identity compatibility mismatch and introduces no new top-level interface, so no additional README text mutation is required for this slice.

## Release rule

This source slice is not a GADI release or activation. Release/tag propagation remains deferred until the parent GADI task satisfies authentic resident runtime execution, closed-loop evidence, reconstruction, and canonical activation predicates.
