# HIL Activation Acceptance Evidence Parity Mirror Handoff

Parent: `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`
Task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
Canonical request: `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`
Cross-task predicate: `PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`
State: `SOURCE_REPAIR_ACTIVE / AUTHENTIC_RUNTIME_CONSUMPTION_NOT_OBSERVED`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`

## Resolved canonical state

The canonical HIL task remains machine-owned and unfinished. The worker registry is `HANDOFF_READY`; the exact resident request remains `REQUESTED`; the canonical resident-consumption predicate remains `UNKNOWN`; authentic `receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json` is not present on canonical repository state; Master Record release remains fail-closed and not ready.

The relevant existing runtime implementation is already present and must be reused:

```text
HB32 independent oscillator / carrier
-> carrier-owned WorkerCoordinator self-heal
-> canonical WorkerCoordinator
-> scripts/dispatch_resident_execution_requests.py
-> scripts/consume_hil_resident_execution_request.py
-> scripts/refresh_and_execute_resident_task.py
-> existing HIL ESRL/materialization/receiver workers
```

No HIL-specific heartbeat, scheduler, WorkerCoordinator, claim/fence plane, credential route, or hosted production runtime is admissible as a substitute.

## Failure corrected

`scripts/run_hil_resident_activation_test.py` is the existing bounded acceptance harness for the first authentic resident HIL activation segment. Its historical issue contract named the required component-produced evidence as:

```text
receipts/sovereign-host/resident-request-dispatch.latest.json
receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json
receipts/sovereign-host/resident-targeted-execution.latest.json
receipts/sovereign-network/hil-intr-ingress.latest.json
receipts/sovereign-host/hil-intr-materialization-consumption.latest.json
receipts/hil-sovereign-receiver/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
```

Before this repair, the harness could report `PASS` without requiring the first two receipts. That created an evidence-semantic false-positive path: downstream materialization/receiver state could satisfy the harness even while the canonical cross-task resident-request-consumption predicate remained unknown.

## Repair

The harness now requires the existing resident dispatcher receipt and exact HIL resident-consumption receipt in addition to the existing ingress, materialization/`LEASE_OPEN`, targeted execution, claim/fence, and receiver-ready evidence.

The dispatcher proof is HIL-specific rather than an aggregate all-consumer success requirement. The dispatcher may retain unrelated request failures because resident consumers are intentionally independent, but its `hil` outcome must prove:

```text
consumer = hil
consumer_ref = scripts/consume_hil_resident_execution_request.py
attempted = true
result.schema = stegverse.hil-resident-execution-request-consumption/v1
result.request_id = RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
result.task_id = SHWP-HIL-SOVEREIGN-RECEIVER-001
result.terminal_hil_transition_observed = true
```

The persisted consumption receipt must independently prove:

```text
schema = stegverse.hil-resident-execution-request-consumption/v1
state = COMPLETED
request_id = RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
task_id = SHWP-HIL-SOVEREIGN-RECEIVER-001
mode = TARGETED_INDEPENDENT_TASK_CONTROL
runtime_execution_attempted = true
terminal_hil_transition_observed = true
terminal_hil_transition = non-empty canonical terminal transition
credential_authority = TV/TVC
github_token_runtime_authority = NONE
heartbeat_grants_execution_authority = false
second_machine_required = false
```

A materialization receipt, receiver receipt, process PID, heartbeat progression, source merge, or CI run cannot substitute for this predicate.

## Preflight and README completeness

Machine preflight:

`receipts/preflight/HIL-ACTIVATION-ACCEPTANCE-EVIDENCE-PARITY-001.json`

The preflight passed before functional mutation and resolved the canonical handoff, worker/task registry, Master Records preparation, cross-task predicate, runtime-solution reuse inventory, collision state, and absent authentic runtime receipts.

README impact is material because the acceptance harness changes evidence semantics and failure behavior. `README.md` is updated in the same change set under `Resident HIL activation acceptance evidence`.

## Authority boundary

This repair changes only what evidence is sufficient for the existing acceptance harness to report `PASS`. It does not create or transfer execution authority, claim/fence authority, transition authority, credential authority, custody authority, review/publication authority, or Master Records authority.

```text
heartbeat_grants_execution_authority = false
WorkerCoordinator retains claim/fence/admission authority
Interlock/InTr retains transition authority
TV/TVC retains credential authority
GitHub token runtime authority = NONE
acceptance receipt authority effect = NONE_TEST_OBSERVATION_ONLY
```

## Current evidence boundary

Source, validation, CI, merge, and this handoff do not establish authentic resident execution. Until a real same-device resident cycle emits the exact request-002 consumption receipt plus the other required component receipts, the canonical cross-task predicate remains `UNKNOWN`, receiver activation remains unproven, TVC lifecycle receiving remains unproven, and Master Record release remains ineligible.

After source validation/merge, the next legitimate transition remains execution through the already-built resident HB32/WorkerCoordinator/dispatcher/HIL-consumer path. No new runtime implementation is required by this repair.
