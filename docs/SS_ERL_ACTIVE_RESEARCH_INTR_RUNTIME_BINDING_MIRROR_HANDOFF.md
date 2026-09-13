# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-13

## Canonical identity

- Goal Task ID: `SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`
- Parent Goal Task: `SS-EVIDENCE-COMPARISON-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CLAIMED_INTEGRATION`
- Completion claimed: `false`
- Completion validated: `false`
- Activation proof complete: `false`

The Goal Task remains valid and is not renamed, restarted, duplicated, or closed.

## Subtraction-first correction

The recent Task Registry convergence layer incorrectly turned coordination visibility into a runtime prerequisite. That gate is not present in the executable ERL path and is removed from the Goal's completion trajectory.

Task Registry remains coordination-only. It may surface adjacent work, including `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`, but adjacency does not import the broader SKAP roundtrip predicates into this narrower ERL path and does not grant or withhold WorkerCoordinator authority.

The active ERL resident-local submitter already:

- uses `STEGOS_RESIDENT_LOCAL`;
- requires no transport credential;
- forbids a TVC relay authorization identifier;
- posts the exact binding to the shared loopback `/intr/materialization` ingress;
- verifies the first two Universal InTr hop receipts and terminal materialization request.

The existing DEVICE_KV consumer already receives that non-authorizing terminal event and invokes the existing `SHWP-DEVICE-KV-INTR-OBSERVATION-001` WorkerCoordinator task path. WorkerCoordinator performs its own claim/fence admission inside the existing execution path. No separate Task Registry `CONTINUE` disposition is required as a runtime precondition.

## Reusable component composition

Canonical composition remains:

1. reusable execution materialization;
2. shared Universal InTr governed ingress;
3. `RTC-MANIFEST-001`;
4. `RTC-INTERLOCK-INTR-TRANSPORT-008` repeated exactly three times;
5. `RTC-FARSIDE-FINAL-009` for terminal KV receive/readback;
6. existing evidence validators;
7. `RTC-EVIDENCE-CUSTODY-004` / Master Records;
8. existing `SHWP-DEVICE-KV-INTR-OBSERVATION-001` runtime-observation owner.

No new scheduler, WorkerCoordinator, listener, credential path, provider operation, heartbeat authority, runtime plane, or user-verification path is created.

## Canonical execution surface

```text
execution surface: CURRENT_USER_IPHONE
remote connected-device requirement: NOT_APPLICABLE
second user-operated device required: false
always-on external host required: false
GitHub runtime authority: NONE
```

Historical connected-device enumeration has no gating meaning for this Goal.

Do **not** poll for, wait for, or require any remotely connected resident device.

## Shortest existing runtime path

```text
ERL resident-local manifest/binding
-> shared loopback Universal InTr ingress
-> EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM
-> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM
-> terminal DEVICE_SYSTEM -> KV materialization request
-> scripts/consume_device_kv_intr_materialization_request.py
-> existing SHWP-DEVICE-KV-INTR-OBSERVATION-001 WorkerCoordinator execution
-> exact terminal KV readback/evidence
-> Master Records custody/reconstruction
```

All three InTr hops must preserve one operation ID, packet ID, acquisition-envelope payload hash, and prior-receipt lineage. The terminal KV leg must durably read back the exact acquisition-envelope bytes.

## Authority model

- Task Registry: coordination only; not a runtime precondition.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority when credentials are actually required; ERL resident-local transport requires none.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes; no user-verification authority.
- Master Records: observed-reality custody/reconstruction authority.
- HeartBeat: synchronization/timing/freshness/liveness/correlation/observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Existing provider proof

The authentic provider proof is fixed and MUST NOT be replayed:

- source ID `ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET`;
- provider file `google-drive:file:1KKBS1drUFVh-czLpmg5koRgDs4YMf-gG`;
- exact size `1015`;
- SHA-256 `94470c58db24e544c3edfcd390cca395375a348879ec3c53451ba517ff917763`.

## Current runtime/evidence state

```text
execution surface: CURRENT_USER_IPHONE
Task Registry runtime gate: NONE
portable DEVICE_KV owner package: SOURCE MATERIALIZED
current-iPhone ERL materialization/execution: NOT OBSERVED
shared loopback ingress for this invocation: NOT OBSERVED
hop 1: NOT OBSERVED
hop 2: NOT OBSERVED
hop 3 / terminal DEVICE_KV execution: NOT OBSERVED
terminal exact-byte KV readback: NOT OBSERVED
Master Records custody/reconstruction: NOT OBSERVED
```

The unresolved class remains `TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_NOT_OBSERVED`.

No authentic current-iPhone execution, InTr admission, hop receipt, terminal KV readback, Master Records custody/reconstruction, or end-to-end completion is claimed.

## Remaining completion predicates

- `ERL_CURRENT_USER_IPHONE_PORTABLE_EXECUTION_SURFACE_BOUND`;
- `ERL_TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_OBSERVED`;
- authentic shared current-device loopback ingress;
- authentic hop 1 / hop 2 / hop 3;
- exact operation/packet/payload/prior-receipt continuity;
- exact terminal KV byte readback;
- complete three-hop chain validation;
- terminal KV proof bound to the existing provider readback without provider replay;
- Master Records custody acceptance and reconstruction confirmation;
- no synthetic receipt, second runtime owner, remote-device dependency, second user-operated device, or device/user-verification substitution.

## Next admissible work

1. Use the existing resident-local ERL materialization/submission path directly; do not insert another Task Registry gate.
2. Observe authentic shared loopback InTr admission and hop 1/hop 2 receipts.
3. Let the admitted terminal materialization event invoke the existing DEVICE_KV consumer and WorkerCoordinator-owned terminal task path.
4. Observe hop 3 and exact terminal KV byte readback.
5. Validate the full chain and bind it to the already-existing provider proof without replay.
6. Submit the authentic chain to the merged Master Records custody interface and require reconstruction confirmation.
7. Reconcile the parent handoff only after those authentic predicates are observed.

## Current state

`CURRENT_IPHONE_RUNTIME_SURFACE_RECONCILED / TASK_REGISTRY_RUNTIME_GATE_REMOVED / SHORTEST_EXISTING_ERL_INTR_DEVICE_KV_PATH_RESTORED / REMOTE_DEVICE_CONNECTOR_NOT_APPLICABLE / REUSABLE_COMPONENT_COMPOSITION_PRESERVED / MASTER_RECORDS_BINDING_MERGED / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED / MASTER_RECORDS_CUSTODY_RECONSTRUCTION_NOT_YET_OBSERVED`
