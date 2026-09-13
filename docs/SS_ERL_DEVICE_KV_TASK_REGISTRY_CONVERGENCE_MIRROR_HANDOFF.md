# ERL / DEVICE_KV Task Registry Convergence Mirror Handoff

Updated: 2026-09-13

Goal Task: `SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`
COSV: `40000100100000`
Runtime truth remains: `docs/SS_ERL_ACTIVE_RESEARCH_INTR_RUNTIME_BINDING_MIRROR_HANDOFF.md`
Authority effect: `NONE_COORDINATION_ONLY`

## Discovery

The portable DEVICE_KV owner package is merged and source-ready through `.github` PR #1735 at `b1530b9dd531c848cc80d6c482ae015653fdd539`.

Portable checkout requires a Task Registry disposition with:

```text
schema = stegverse.task-registry-checkin-disposition/v1
task_id = SHWP-DEVICE-KV-INTR-OBSERVATION-001
disposition = CONTINUE
authority_effect = NONE
```

WorkerCoordinator remains the only claim/fence authority after that coordination-only gate.

Before this reconciliation, `SHWP-DEVICE-KV-INTR-OBSERVATION-001` existed in the worker registry, executable handoff, task vector, process adapter, and portable package but did not have a canonical record under `data/canonical-task-records/`. The generic Task Registry evaluator would therefore return `STOP_NOT_REGISTERED`.

This reconciliation registers that **existing owner** under the same task ID and COSV `50000000101000`. It does not create a new Goal Task, worker, scheduler, authority path, or runtime owner.

## Current convergence collision

After registration, immediate portable checkout is still not admissible.

`STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` is currently:

```text
coordination_state = ACTIVE
checkout_state = CHECKED_OUT
```

and canonically names `SHWP-DEVICE-KV-INTR-OBSERVATION-001` as an adjacent task.

The roundtrip Goal is broader:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

The ERL Goal requires only its own three-hop path ending at KV:

```text
EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV
```

The roundtrip task is currently waiting on authentic current-iPhone TVC/SKAP prerequisites that are not ERL completion predicates. ERL therefore MUST NOT inherit those predicates merely because both trajectories touch DEVICE/KV.

However, because the roundtrip task is already checked out and adjacency is canonical, this session also MUST NOT force Task Registry `CONTINUE`, weaken collision detection, delete the adjacency, or mint a competing WorkerCoordinator claim/fence for the DEVICE_KV owner.

## Correct current disposition

The correct coordination state is:

```text
DEVICE_KV_OWNER_REGISTERED_IN_TASK_REGISTRY
PORTABLE_DEVICE_KV_PACKAGE_MERGED
CURRENT_USER_IPHONE_SURFACE_MERGED
ACTIVE_ADJACENT_DEVICE_KV_SKAP_ROUNDTRIP_CHECKOUT_OBSERVED
TASK_REGISTRY_CONTINUE_NOT_YET_ADMISSIBLE
COORDINATE_CONVERGENCE_REQUIRED
```

This is a coordination result only. It does not prove execution of either Goal Task.

## Authority invariants

- Task Registry remains coordination-only and cannot mint execution authority.
- WorkerCoordinator remains claim/fence authority.
- Interlock/InTr remains transition/admission authority.
- TV/TVC remains credential/provider/release authority.
- KV/SKAP Vault remains sole user-verification authority.
- StegOS/current-iPhone identity is not user-verification authority.
- GitHub runtime authority remains `NONE`.
- Provider replay remains unauthorized.
- Remote-device enumeration remains `NOT_APPLICABLE`.
- A second user-operated device remains prohibited.

## Next admissible work

Resolve the canonical adjacency through existing cross-task coordination before portable checkout. The resolution must preserve the already-checked-out roundtrip owner, prove whether ERL can consume a narrower DEVICE_KV evidence-producing step without competing for the roundtrip claim/fence, and express any remaining subject-bound evidence delta precisely.

Until that coordination resolves to a Task Registry `CONTINUE` disposition for `SHWP-DEVICE-KV-INTR-OBSERVATION-001`, do not invoke portable WorkerCoordinator checkout for this ERL trajectory.
