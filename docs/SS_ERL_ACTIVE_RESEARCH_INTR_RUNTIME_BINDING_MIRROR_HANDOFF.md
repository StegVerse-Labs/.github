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

The Goal Task remains valid. It is not renamed, restarted, duplicated, or closed by this runtime-surface/package reconciliation.

## Reusable component composition

The canonical Reusable Task Component Model remains the model merged through `.github` PR #1652 at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`; Goal-specific componentization remains PR #1658 at `39ddc61a0e2528970278b8278d5c1e1222b55ca4`.

Selected components remain:

1. reusable execution materialization;
2. shared Universal InTr governed ingress;
3. `RTC-MANIFEST-001`;
4. `RTC-INTERLOCK-INTR-TRANSPORT-008` repeated exactly three times;
5. `RTC-FARSIDE-FINAL-009` for terminal KV receive/readback;
6. existing evidence validators;
7. `RTC-EVIDENCE-CUSTODY-004` / Master Records;
8. existing `SHWP-DEVICE-KV-INTR-OBSERVATION-001` runtime-observation owner.

No new scheduler, WorkerCoordinator, listener, credential path, provider operation, heartbeat authority, runtime plane, or user-verification path is created.

## Current-iPhone execution surface

The connected/authorized resident-device enumeration gate is superseded and `NOT_APPLICABLE` for this Goal Task.

Canonical execution surface:

```text
execution surface: CURRENT_USER_IPHONE
WorkerCoordinator authority: StegVerse-Labs/.github WorkerCoordinator
StegOS role: subordinate bounded transport/execution adapter
second user-operated device required: false
always-on external host required: false
remote-device connector required: false
GitHub runtime authority: NONE
```

The governing portable authority contract is `docs/WORKERCOORDINATOR_PORTABLE_IPHONE_EXECUTION_MIRROR_HANDOFF.md`.

Historical zero-device connector observations remain provenance only and have no gating meaning.

Do **not** poll for, wait for, or require any remotely connected resident device.

## Portable DEVICE_KV owner package

This source trajectory adds the missing canonical portable package for the already-existing terminal runtime owner:

`control/portable-workercoordinator-packages/device-kv-intr-observation.json`

The package does **not** create an ERL-specific WorkerCoordinator task. It packages the existing canonical owner `SHWP-DEVICE-KV-INTR-OBSERVATION-001`, whose worker registry and executable handoff are already `HANDOFF_READY` / authorized for independent task control.

The package reuses:

- portable authority epoch `WC-PORTABLE-IPHONE-20260902`;
- current historical portable fencing floor greater than G24;
- worker `device-kv-intr-observation-worker`;
- capabilities `runtime_observation`, `bounded_process_execution`, `durable_state_reconstruction`;
- exact current source bindings for the DEVICE_KV worker-registry fragment, executable handoff, state vector, and portable checkout implementation;
- existing event-triggered `workers/universal_intr_profiled_ingress.py` -> `scripts/consume_device_kv_intr_materialization_request.py` path.

The event/materialization binding grants no authority, mints no claim/fence, requires no always-on receiver, and requires no second user device.

The ERL-specific `control/resident-execution-request.d/erl-active-research-intr-runtime-binding-001.json` remains a non-authorizing invocation payload. It identifies this Goal Task/COSV and selects `SHWP-DEVICE-KV-INTR-OBSERVATION-001` as the terminal runtime owner without creating a parallel authority task.

Package source materialization is **not** checkout evidence. `runtime_execution_observed=false` and `activation_effect=false` remain required until authentic current-iPhone execution occurs.

## Authority model

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes; no user-verification authority.
- Master Records: observed-reality custody/reconstruction authority.
- HeartBeat: synchronization/timing/freshness/liveness/correlation/observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

Runtime subject binding, current-iPhone identity, node identity, transport identity, or Secure Enclave identity do not become user-verification authority.

## Logical transport path

```text
EXTERNAL_SYSTEM
-> STEGOS_ECOSYSTEM
-> DEVICE_SYSTEM
-> KV
```

The three reusable InTr component instances remain:

1. `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM`;
2. `STEGOS_ECOSYSTEM -> DEVICE_SYSTEM`;
3. `DEVICE_SYSTEM -> KV`.

All three must retain one operation ID, packet ID, acquisition-envelope payload hash, and prior-receipt lineage. The terminal KV leg must durably read back the exact acquisition-envelope bytes.

## Existing provider proof

The authentic provider proof is fixed and MUST NOT be replayed:

- source ID `ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET`;
- provider file `google-drive:file:1KKBS1drUFVh-czLpmg5koRgDs4YMf-gG`;
- exact size `1015`;
- SHA-256 `94470c58db24e544c3edfcd390cca395375a348879ec3c53451ba517ff917763`.

## Merged source floor before this package

- #1585 `fd1d7b3f3d42c6bb2fe1bb59838121f45ace5a55`: resident-local transport correction and retained-source convergence;
- #1605 `c6434d85a89a0cc283bdfc1262411152ecf6ae13`: exact receipt/request proof hardening;
- #1645 `e6fa3c2de5c89c1668d91b5815dbc71a1969b860`: durable submission-dispatch reconstruction evidence;
- #1648 `8a1ffeeb223a3d6125caebafd22cfbd8fc58f34d`: terminal full-intent identity continuity and exact KV byte-readback path;
- Executive_Rhetoric_Ledger #158 `f827ffe1f46294c89b073b34fbe491b31254596f`: existing provider-proof projection and fail-closed binding verifier;
- #1658 `39ddc61a0e2528970278b8278d5c1e1222b55ca4`: reusable-component reconciliation;
- master-records/orchestration #94 `560863ff192f4437911a8d748984d06566c120c7`: generic Universal InTr chain custody/reconstruction;
- #1725 `68b43a93931b8957a54c1fe7882b2402980a1813`: ERL-to-Master-Records binding;
- #1728 `17dd7c870a5261177980a2809b33de73a4b29e4f`: Task Registry custody-binding reconciliation;
- #1732 `96f085396a65f31026c61e1b413b69567bb4f906`: current-iPhone runtime-surface correction and remote-device-gate retirement.

These prove source construction/compatibility only, not authentic ERL execution.

## Current runtime/evidence state

Correct unresolved classification:

```text
execution surface: CURRENT_USER_IPHONE
remote connected-device requirement: NOT_APPLICABLE
second user-operated device requirement: false
always-on external host requirement: false
portable DEVICE_KV owner package: SOURCE MATERIALIZED
portable WorkerCoordinator checkout/claim/fence for this execution: NOT OBSERVED
current-iPhone ERL materialization/execution: NOT OBSERVED
shared current-device loopback ingress for this invocation: NOT OBSERVED
hop 1: NOT OBSERVED
hop 2: NOT OBSERVED
hop 3: NOT OBSERVED
terminal exact-byte KV readback: NOT OBSERVED
Master Records custody/reconstruction for this chain: NOT OBSERVED
```

The unresolved class remains `TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_NOT_OBSERVED`.

No authentic checkout, current-iPhone execution, InTr admission, hop receipt, terminal KV readback, Master Records custody/reconstruction, or end-to-end completion is claimed.

## Remaining completion predicates

- `ERL_CURRENT_USER_IPHONE_PORTABLE_EXECUTION_SURFACE_BOUND`;
- `DEVICE_KV_CURRENT_IPHONE_PORTABLE_PACKAGE_AVAILABLE`;
- `ERL_TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_OBSERVED`;
- authentic task/COSV-bound WorkerCoordinator checkout/claim/fence;
- authentic shared current-device loopback ingress;
- authentic hop 1 / hop 2 / hop 3;
- exact operation/packet/payload/prior-receipt continuity;
- exact terminal KV byte readback;
- complete three-hop chain validation;
- terminal KV proof bound to the existing provider readback without provider replay;
- Master Records custody acceptance and reconstruction confirmation;
- no synthetic receipt, second runtime owner, remote-device dependency, second user-operated device, or device/user-verification substitution.

## Next admissible work

1. Validate and merge the portable DEVICE_KV owner package and canonical references.
2. On the `CURRENT_USER_IPHONE` execution surface, consume the canonical Task Registry `CONTINUE` disposition and perform portable WorkerCoordinator checkout of `SHWP-DEVICE-KV-INTR-OBSERVATION-001` using the existing authority lineage.
3. Bind the already-existing ERL request/COSV to that checked-out owner without minting another claim/fence.
4. Materialize exact local source and observe the shared current-device loopback ingress.
5. Execute the three reusable InTr hops and exact terminal KV readback.
6. Validate the complete chain and provider-proof binding without replay.
7. Submit authentic evidence to the merged generic Master Records custody interface and require reconstruction confirmation.
8. Reconcile the parent handoff only after those authentic predicates are observed.

## Current state

`CURRENT_IPHONE_RUNTIME_SURFACE_RECONCILED / DEVICE_KV_PORTABLE_OWNER_PACKAGE_SOURCE_MATERIALIZED / REMOTE_DEVICE_CONNECTOR_NOT_APPLICABLE / REUSABLE_COMPONENT_COMPOSITION_PRESERVED / MASTER_RECORDS_BINDING_MERGED / TASK_BOUND_NATIVE_IPHONE_CHECKOUT_AND_EXECUTION_NOT_YET_OBSERVED / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED / MASTER_RECORDS_CUSTODY_RECONSTRUCTION_NOT_YET_OBSERVED`
