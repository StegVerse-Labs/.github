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
- reacquisition reason: INITIAL, REQUIRED_STATE_CHANGED, PASSBAND_CROSSED, or NONE_TERMINAL;
- explicit authority effect NONE.

## Reacquisition semantics

A new snapshot is acquired when:

1. there is no prior snapshot; or
2. at least one required state remains unresolved and its observed state/evidence changes; or
3. at least one required state remains unresolved and the carrier reference moves beyond the configured passband relative to the prior snapshot.

When all required states are complete, the gate closes and periodic reacquisition stops for that monitored goal. A later explicit goal/revision may open a new snapshot chain; it does not rewrite the closed chain.

Snapshot reacquisition samples the current carrier reference. It does not create, increment, suppress, delay, authorize, or otherwise control that reference.

## Current target integration

The first configured monitor targets `SHWP-DURABLE-RUNTIME-ACTIVATION` and observes, without owning:

- corrected oscillator-backed carrier evidence;
- task-capable WorkerCoordinator evidence required by the G18/runtime goal;
- terminal G18/runtime-goal state.

Independent orphan recovery remains a separate task-control goal and must not be made an authority prerequisite for heartbeat progression. A separate snapshot monitor may observe that goal independently.

## Required implementation

```text
heartbeat_runtime/reference_snapshot.py
schemas/heartbeat-reference-snapshot.schema.json
control/heartbeat-reference-snapshot-policy.json
scripts/reacquire_heartbeat_reference_snapshot.py
tests/test_reference_snapshot_reacquisition.py
```

Integration may update the runtime separation/continuity contracts and canonical handoffs only to document this monitoring interpretation. It must not alter `heartbeat_runtime/independent_oscillator.py` or make snapshot logic causal to carrier progression.

## Completion

Source completion requires deterministic tests proving:

- initial snapshot acquisition;
- no reacquisition when unresolved states and carrier remain inside passband with no state change;
- reacquisition on required-state progress;
- reacquisition after passband crossing while unresolved;
- terminal gate closure when every required state is complete;
- closed snapshot chains do not periodically reacquire;
- snapshot chain hashes bind prior/current references and state observations;
- no snapshot operation grants heartbeat/task/claim/fence/credential authority.

Live activation remains separate: source installation does not prove that a runtime owner has begun producing these snapshots.
