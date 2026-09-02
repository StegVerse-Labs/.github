# GATE/PASSBAND Reference Snapshot Mirror Handoff

Updated: 2026-08-18T19:21:00-05:00

## Goal

```text
goal_id: GATE-PASSBAND-REFERENCE-SNAPSHOT-010
repository: StegVerse-Labs/.github
canonical_parent: StegVerse-Labs/.github#122
carrier_owner: HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122
credential_authority: TV/TVC
primary_runtime: StegVerse
third_party_role: FALLBACK_ONLY
state: COMPLETE_VALIDATED_SUPERSEDED_MONITOR
```

Redefine `snapshot` within the historical `GATE_PASSBAND_DERIVED` boundary so the term no longer means a static persisted heartbeat ordinal or a mechanism that advances heartbeat. It means a chained, non-authorizing **reference snapshot** used to monitor progress of required states toward completion.

## Boundary

The carrier remains governed by the independent oscillator contract:

```text
carrier progression: OSCILLATOR_ONLY
phase travel: 10 ms
observation_is_causal: false
snapshot may advance carrier: false
snapshot may delay carrier: false
snapshot may grant task/claim/fence authority: false
```

`GATE_PASSBAND_DERIVED` is retained only as a **snapshot reacquisition policy**.

## Redefined snapshot

A reference snapshot contains:

- the currently observed carrier reference/generation;
- a stable identity/hash for the snapshot;
- a pointer/hash to the previous snapshot when one exists;
- the required state set for the monitored goal;
- each state's observed value, completion predicate, evidence refs, and COMPLETE/PENDING result;
- gate state: OPEN while any required state is unresolved, CLOSED only when every required state is evidenced complete;
- passband state: the maximum permitted carrier-reference delta before unresolved state must be re-observed;
- reacquisition reason: INITIAL, REFERENCE_REPAIR, REQUIRED_STATE_CHANGED, PASSBAND_CROSSED, TERMINAL_GATE_CLOSED, or no reacquisition when NONE_TERMINAL / WITHIN_PASSBAND_NO_STATE_CHANGE;
- explicit authority effect NONE.

## Reacquisition semantics

A new snapshot is acquired when:

1. there is no prior snapshot; or
2. at least one required state remains unresolved and its observed state/evidence changes; or
3. at least one required state remains unresolved and the carrier reference moves across the configured passband relative to the prior snapshot; or
4. the final pending state completes, producing a terminal gate-closing snapshot.

When all required states are complete, the gate closes and periodic reacquisition stops for that monitored goal. A later explicit goal/revision may open a new snapshot chain; it does not rewrite the closed chain.

Snapshot reacquisition samples the current carrier reference. It does not create, increment, suppress, delay, authorize, or otherwise control that reference.

## Implemented source

```text
heartbeat_runtime/reference_snapshot.py
  commit: 8b7716700d4e542e0e361279aef05fdd1516a393
schemas/heartbeat-reference-snapshot.schema.json
  commit: a2bad7050f8bc32a0faa6c571a7ce9a437de0396
control/heartbeat-reference-snapshot-policy.json
  commit: b9823267d629690c71885b1a5e54d9d4a226c449
scripts/reacquire_heartbeat_reference_snapshot.py
  commit: 6b7f6b6a296726360e5bfd111c2c52e3948b2ff2
tests/test_reference_snapshot_reacquisition.py
  commit: 89c9afd5e5772bf351a347186ad6d2eed4a4def9
control/runtime-separation-contract.json
  commit: b9603d8b944b514cd977b911cafdc32138b4bb5c
management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json
  commit: fd6b30de95de95b78d5c9752fc4309ff06f032d1
docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md
  commit: 5b969eed9ade3c8afb011622a6a7698fe333e98e
```

No change was made to `heartbeat_runtime/independent_oscillator.py`.

## Current configured monitor

The first monitor targets `SHWP-DURABLE-RUNTIME-ACTIVATION` and observes, without owning:

1. corrected oscillator-backed carrier evidence;
2. task-capable WorkerCoordinator evidence required by the G18/runtime goal;
3. terminal G18/runtime-goal state with claim/worker binding released.

Independent orphan recovery remains a separate task-control goal and is not an authority prerequisite for heartbeat progression. A separate snapshot monitor may observe that goal independently.

Policy:

```text
control/heartbeat-reference-snapshot-policy.json
monitor_id: SHWP-DURABLE-RUNTIME-ACTIVATION-REFERENCE-MONITOR
passband_width_references: 1
```

The width is expressed in carrier references, not wall-clock authority. State change may force an earlier reacquisition inside the passband.

## Initial reacquired snapshot

The first monitoring snapshot is now durable:

```text
latest: control/heartbeat-reference-snapshot.json
history: receipts/heartbeat-reference-snapshots/SHWP-DURABLE-RUNTIME-ACTIVATION-REFERENCE-MONITOR-31-165ceac24cfddfe7.json
snapshot_id: SHWP-DURABLE-RUNTIME-ACTIVATION-REFERENCE-MONITOR:31:165ceac24cfddfe7
snapshot_sha256: 611bf71f0e954603127c2841143519704977182e4d5f26e0ae23f1463c2a8262
reference: heartbeat_epoch:31
observed carrier frequency label: GATE_PASSBAND_DERIVED
reacquisition rule: GATE_PASSBAND_DERIVED
gate: OPEN
complete: 0/3
pending: 3/3
authority_effect: NONE
```

This snapshot does **not** rewrite or upgrade HB31. It records HB31 as the first current monitoring reference. The historical carrier still lacks corrected oscillator proof, the task-capable worker predicate is not yet present in the current transition receipt, and G18 remains nonterminal with its old claim/worker binding. The gate therefore correctly remains OPEN.

## Validation contract

Deterministic tests are installed to prove:

- initial snapshot acquisition;
- no reacquisition when unresolved states remain inside passband with no state change;
- reacquisition on required-state progress;
- reacquisition after passband crossing while unresolved;
- terminal gate closure when every required state is complete;
- closed snapshot chains do not periodically reacquire;
- carrier reference regression fails closed;
- snapshot chain hashes bind prior/current observations;
- historical `GATE_PASSBAND_DERIVED` carrier state may be observed without rewrite;
- no snapshot operation grants heartbeat/task/claim/fence/credential authority.

Exact-head hosted validation is **not yet observed**. `get_commit_combined_status` for canonical handoff head `5b969eed9ade3c8afb011622a6a7698fe333e98e` returned no statuses. Therefore source implementation is installed, but validation remains open.

## Live activation distinction

The initial snapshot has been acquired from current durable repository evidence. That is monitoring activation only. It is **not** corrected oscillator runtime activation and does not satisfy the pending runtime goals.

The snapshot chain becomes useful precisely because required state can now be monitored without freezing completion analysis at historical HB31. On the next invocation of `scripts/reacquire_heartbeat_reference_snapshot.py`:

- if the carrier reference changes beyond the passband while states remain unresolved, a new snapshot is acquired;
- if any required state changes before that, a new snapshot is acquired immediately;
- if all required states complete, a final CLOSED snapshot is acquired and periodic monitoring stops.

## Collision boundaries

Do not create another heartbeat or scheduler. Do not let snapshot logic become carrier timing authority. Do not mutate G18/G20/recovery claims/fences through snapshot evaluation. Do not change protected credential/route/wallet state. StegVerse remains primary; third parties remain fallback-only; TV/TVC remains sole credential authority.

## Completion accounting

```text
snapshot semantic redefinition: COMPLETE_SOURCE
snapshot implementation/schema/policy/runner/tests: 5/5 IMPLEMENTED
runtime/continuity contract reconciliation: COMPLETE_SOURCE
initial monitoring snapshot: ACQUIRED
initial gate state: OPEN 0/3
exact-head deterministic execution evidence: PENDING
live corrected oscillator evidence: PENDING MACHINE EXECUTION
snapshot-chain next reacquisition: PENDING STATE/REFERENCE CHANGE
archive eligible: false while validation and monitored runtime states remain nonterminal
```


## 2026-09-02 supersession closure

The reference-snapshot **mechanism** remains valid and tested, but its first configured monitor is no longer a lawful current completion gate.

The preserved initial chain targeted historical `SHWP-DURABLE-RUNTIME-ACTIVATION` predicates, including a task-capable G18 cycle and terminal G18 state. Subsequent canonical corrections established:

```text
heartbeat protocol: ACTIVE_PROTOCOL_VERIFIED
heartbeat progression: OSCILLATOR_ONLY
G18 terminalization required for downstream admission: false
worker/task state causal to heartbeat progression: false
downstream HB32 consumer propagation: COMPLETE (#263)
```

Therefore the historical OPEN 0/3 chain is retained unchanged as provenance and is **superseded**, not rewritten into a false CLOSED snapshot. Periodic reacquisition of that obsolete monitor is no longer a current requirement.

`GATE_PASSBAND_DERIVED` remains available solely as a non-authorizing snapshot-reacquisition mechanism for a future explicitly revised monitor. Such a future goal must create a new policy revision/chain rather than reopening this historical one.

Current source goal status:

```text
semantic redefinition: COMPLETE
implementation/schema/policy/runner/tests: COMPLETE
current validation: PASS
historical first monitor: SUPERSEDED_PRESERVED_OPEN
heartbeat activation dependency: NONE
G18 downstream dependency: NONE
archive eligible: true
authority effect: NONE
```
