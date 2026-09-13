# SDK WorkSpace External-Collaboration Authentic Runtime 004 Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Parent Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV: `71000000100110`
Status: `ACTIVE / NODE + KV CONTINUITY RECONCILED / TASK-BOUND NODE EXECUTION EVIDENCE REQUIRED`

## Purpose and identity

This remains the canonical runtime-evidence handoff for the active Goal Task. Goal identity, COSV, authority separation, reusable-component composition, and evidence-class discipline are preserved.

## Canonical device / Node / KV model

`data/task-registry-global-invariants.json` is controlling for this distinction:

- StegOS devices are `INTERCHANGEABLE_TRANSPORT_NODE` surfaces;
- physical-device identity, device attestation, connector inventory, or device connectivity are not verification or task-completion gates;
- replacing one eligible device/node with another does not change the user verifier;
- Node identity is runtime/evidence correlation only and does not confer user identity or authority;
- KV/SKAP Vault is the sole user-verification authority;
- a Node may invoke local capabilities only after applicable KV/SKAP-backed user-verification state and Interlock/InTr admission are bound to the exact operation.

Accordingly, the Goal Task is **not bound to an iPhone, another physical device, a Remote Desktop connection, or any persistent device identity**.

The execution prerequisite is:

```text
an eligible StegOS-capable device
-> establish or recover a StegVerse Node
-> bind applicable KV/SKAP-backed continuity/user-verification state
-> WorkerCoordinator claim/fence when required
-> Interlock/InTr admission for the exact governed operation
-> bounded execution
-> authentic task-bound receipts
```

The physical device on which that Node is materialized is execution metadata only. It may change without changing Goal identity, user-verification authority, or completion semantics.

## Superseded runtime-surface framings

Two earlier framings are retained only as provenance:

1. `UNRESOLVED_NO_CURRENT_AUTHORIZED_DEVICE` / remote resident reconnection — invalid because no connected resident device is required.
2. `CURRENT_USER_IPHONE` as the selected Goal execution surface — too specific because the hardware is interchangeable once the Node is established/recovered.

Historical receipts may truthfully record that a particular execution happened on an iPhone. That fact must never become a prerequisite for this Goal Task.

Current classification:

`TASK_BOUND_ESTABLISHED_NODE_EXECUTION_EVIDENCE_NOT_OBSERVED`

## Authority separation

Task Registry coordinates only. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns credential/provider/release authority. KV/SKAP Vault is the sole user-verification authority and continuity source for applicable user state. StegOS devices are interchangeable execution/transport surfaces. Node identity is correlation only. Master Records owns observed reality/custody/reconstruction. HeartBeat owns timing/freshness/liveness/correlation/observability only. GitHub has no runtime authority.

## Reusable component composition

The Reusable Task Component Model merged through PR #1652 at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`. This Goal continues through the existing runtime-observation owner, `RTC-MANIFEST-001`, reusable ephemeral execution materialization, repeatable `RTC-INTERLOCK-INTR-TRANSPORT-008`, repeatable `RTC-ROUNDTRIP-003`, existing TV/TVC provider/session handling, existing evidence validators, `RTC-EVIDENCE-CUSTODY-004`, `RTC-SDK-RETURN-006` when required, and conditional Publisher/egress/far-side components only when their predicates are reached.

No new reusable component is required. Device selection is not a reusable authority-bearing component. The established Node consumes the already-existing component chain.

## Current runtime/evidence state

The task-specific source path remains available, but authentic execution of this Goal has not been observed.

```text
eligible physical device requirement: ANY SUPPORTED STEGOS-CAPABLE DEVICE
established/recovered Node required: YES
physical-device identity gate: PROHIBITED
specific-iPhone requirement: NOT_APPLICABLE
remote connected-device requirement: NOT_APPLICABLE
KV/SKAP-backed operation state: REQUIRED WHEN THE OPERATION REQUIRES USER/SECRET CONTINUITY
task-bound established-Node execution: NOT OBSERVED
WorkerCoordinator claim/fence for this execution: NOT OBSERVED
Interlock/InTr admission for this execution: NOT OBSERVED
resident reseal consumption receipt: NOT OBSERVED
resident consent-listener consumption receipt: NOT OBSERVED
external-collaboration target custody/readback: NOT PROVEN
```

The absence of those task-bound receipts is the unresolved evidence condition. The identity or model of the physical device is irrelevant.

## Remaining Goal predicates

- `AUTHENTIC_POST_MERGE_RESIDENT_LIFECYCLE_INVOCATION_OBSERVED`
- `SAME_INVOCATION_REUSABLE_LIFECYCLE_CHAIN_PROVEN`
- `UTC_HOUR_SLOT_SATISFACTION_WITHOUT_DUPLICATE_EXECUTION_PROVEN`
- `RESIDENT_RESEAL_CONSUMPTION_RECEIPT_OBSERVED`
- `RESIDENT_CONSENT_LISTENER_CONSUMPTION_RECEIPT_OBSERVED`
- `EXTERNAL_COLLAB_CLIENT_SECRET_CUSTODY_PROVEN`
- `SOVEREIGN_CALLBACK_REACHABILITY_PROVEN`
- `OWNER_PRESENT_GOOGLE_CONSENT_PROVEN`
- `AUTHORITATIVE_PROVIDER_FILE_PROBE_PROVEN`
- `SDK_ACTIVE_PROBE_COMPLETE_PREDICATE_REEVALUATION_PROVEN`
- `MIR_TRANSITION_REPORTING_PROVEN`
- `MASTER_RECORDS_CUSTODY_RECONSTRUCTION_PROVEN`
- `ESTABLISHED_NODE_END_TO_END_PROVEN`
- `DOWNSTREAM_PROPAGATION_COMPLETE`
- `PUBLIC_DISTRIBUTIONS_COMPLETE`

`ONE_CURRENT_DEVICE_END_TO_END_PROVEN` is superseded for this active Goal because hardware identity is not a completion semantic. Historical parent records retain the old wording as provenance only.

## Next admissible work

Bind the existing Goal Task/COSV and already-local external-collaboration requests to the canonical **established-Node** execution path. Reuse whatever eligible StegOS-capable device is materializing the Node; do not select or pin hardware as part of admission.

For the reseal operation, resolve the applicable KV/SKAP custody state and preserve the existing rule that provider/storage possession does not itself confer plaintext/use authority. For both reseal and listener work, require the exact WorkerCoordinator and Interlock/InTr transitions that apply, execute through the established Node, and retain the resulting task-bound receipts.

Continue component-by-component until a real authority, evidence, provider, or human boundary is reached. Do not wait for a connected device. Do not require an iPhone specifically. Do not create device verification, a second user-operated-device requirement, or a new runtime authority plane.

## README review

No README change is required. The global invariant already defines device interchangeability, KV/SKAP user-verification exclusivity, Node non-authority semantics, and prohibition of physical-device identity gates.

## Human action

None.
