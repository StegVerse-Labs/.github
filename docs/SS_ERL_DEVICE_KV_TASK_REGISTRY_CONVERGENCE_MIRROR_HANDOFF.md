# ERL / DEVICE_KV Task Registry Convergence Mirror Handoff

Updated: 2026-09-13

Goal Task: `SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`
COSV: `40000100100000`
Runtime truth remains: `docs/SS_ERL_ACTIVE_RESEARCH_INTR_RUNTIME_BINDING_MIRROR_HANDOFF.md`
Authority effect: `NONE_COORDINATION_ONLY`

## Subtraction-first reconciliation

The prior version of this handoff incorrectly promoted a Task Registry `CONTINUE` disposition into a runtime prerequisite before the existing DEVICE_KV owner could be used by the ERL trajectory.

That requirement is removed.

Canonical executable source already establishes the shorter path:

```text
ERL resident-local manifest/binding
-> shared loopback Universal InTr ingress
-> hop 1
-> hop 2
-> terminal DEVICE_SYSTEM -> KV materialization request
-> scripts/consume_device_kv_intr_materialization_request.py
-> existing SHWP-DEVICE-KV-INTR-OBSERVATION-001 WorkerCoordinator task execution
-> exact terminal KV readback/evidence
```

The resident-local ERL submitter explicitly uses `STEGOS_RESIDENT_LOCAL`, requires no transport credential, and forbids a TVC relay authorization identifier. The DEVICE_KV consumer receives a non-authorizing admitted materialization event and invokes the already-existing bounded WorkerCoordinator task path. WorkerCoordinator remains responsible for claim/fence admission inside that path.

## Task Registry role

The Task Registry record for `SHWP-DEVICE-KV-INTR-OBSERVATION-001` remains useful for coordination, discovery, collision visibility, and fresh-state reconciliation. It does not grant runtime authority and is not an additional runtime gate.

A `COORDINATE_CONVERGENCE` result involving `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` therefore means only that adjacent work exists. It does not make the broader SKAP roundtrip task's prerequisites part of the narrower ERL completion path and does not prohibit the ERL event from reaching the existing DEVICE_KV owner through its canonical admitted-event execution path.

No adjacency is deleted, no competing WorkerCoordinator is created, and no claim/fence is minted by Task Registry.

## Authority invariants

- Task Registry: coordination only; not a runtime precondition.
- WorkerCoordinator: sole claim/fence authority for the bounded DEVICE_KV task.
- Interlock/InTr: transition/admission authority.
- TV/TVC: credential/provider/release authority when a transition actually requires credentials; the ERL resident-local transport leg does not.
- KV/SKAP Vault: sole user-verification authority.
- GitHub: source/evidence coordination only; runtime authority `NONE`.
- Remote-device enumeration: `NOT_APPLICABLE`.
- Second user-operated device: prohibited/not required.
- Provider replay: unauthorized.

## Current disposition

```text
DEVICE_KV_OWNER_REGISTERED_IN_TASK_REGISTRY
PORTABLE_DEVICE_KV_PACKAGE_MERGED
CURRENT_USER_IPHONE_SURFACE_MERGED
ADJACENT_DEVICE_KV_SKAP_ROUNDTRIP_VISIBLE_FOR_COORDINATION
TASK_REGISTRY_RUNTIME_GATE = NONE
SHORTEST_EXISTING_ERL_EVENT_PATH_RESTORED
AUTHENTIC_CURRENT_IPHONE_EXECUTION_EVIDENCE_NOT_YET_OBSERVED
```

## Next admissible work

Use the existing ERL resident-local input/materialization path directly. Observe the shared loopback InTr admission, the two upstream receipts, the terminal DEVICE_KV materialization event, the existing WorkerCoordinator-owned terminal execution, exact KV byte readback, and then Master Records custody/reconstruction. Do not add another scheduler, Task Registry gate, transport credential, remote-device dependency, runtime owner, or coordination layer.
