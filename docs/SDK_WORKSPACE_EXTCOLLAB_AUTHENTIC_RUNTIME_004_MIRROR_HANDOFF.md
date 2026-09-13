# SDK WorkSpace External-Collaboration Authentic Runtime 004 Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Parent Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV: `71000000100110`
Status: `ACTIVE / RTC-RESIDENT-RENDEZVOUS-010 SOURCE MERGED + VALIDATED / AUTHENTIC TASK-BOUND NODE EXECUTION EVIDENCE REQUIRED`

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

Accordingly, the Goal Task is not bound to an iPhone, another physical device, a Remote Desktop connection, or any persistent device identity.

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

Task Registry coordinates only. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns credential/provider/release authority. KV/SKAP Vault is the sole user-verification authority and continuity source for applicable user state. StegOS devices are interchangeable execution/transport surfaces. Node identity is correlation/routing only. Master Records owns observed reality/custody/reconstruction. HeartBeat owns timing/freshness/liveness/correlation/observability only. GitHub has no runtime authority.

## Reusable component composition

The Reusable Task Component Model merged through PR #1652 at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

The Goal transport profile selects `RTC-RESIDENT-RENDEZVOUS-010` only for these two resident-delivery round trips:

- `resident_client_secret_reseal`
- `resident_consent_listener`

This is the existing canonical non-authorizing established-Node request-delivery component. It provides target-node routing, exact inner-request digest binding, delivery acknowledgement, and transport-only correlation. It does not grant user verification, WorkerCoordinator claim/fence, Interlock/InTr admission, TV/TVC credential/provider/release authority, or Master Records custody/reconstruction authority.

The rest of the Goal continues through `RTC-MANIFEST-001`, reusable bounded execution materialization, repeatable `RTC-INTERLOCK-INTR-TRANSPORT-008`, repeatable `RTC-ROUNDTRIP-003`, existing TV/TVC provider/session handling, existing evidence validators, `RTC-EVIDENCE-CUSTODY-004`, `RTC-SDK-RETURN-006` when required, and conditional Publisher/egress/far-side components only when their predicates are reached.

No new reusable component is required.

## Resident-rendezvous source completion

The previously identified consumer-registration gap is source-complete and validated on both canonical owners.

Resident side (`StegVerse-Labs/.github`):

- PR #1756 merged at `8770a4007e72f7d407b37b9675916d2121c7c1b2`;
- Organization Control run `34779449112` PASS;
- Deterministic Repository Suite run `34779449080` PASS;
- Heartbeat Worker Project run `34779449072` PASS;
- exact request validation is registered for `sdk_workspace_external_collab_client_secret_reseal` and `sdk_workspace_external_collab_consent_listener`;
- existing lower-level resident consumers remain authoritative for their operation-specific request shape and execution result;
- reseal terminals `COMPLETED` and `TARGET_ALREADY_PRESENT` map to terminal rendezvous completion; listener terminals `COMPLETED` and `SERVICE_ALREADY_HEALTHY` map to terminal rendezvous completion; `BLOCKED` remains fail-closed;
- listener non-secret configuration survives the rendezvous environment sanitizer without introducing credential-bearing transport.

Service Gateway side (`StegVerse-org/LLM-adapter`):

- PR #337 merged at `ded63a597140a27f39469b77f8ad0e04b1fc4eef`;
- Work Mutation Safety run `34779030889` PASS;
- validation run `34779030902` PASS;
- both exact resident request shapes are admitted through the existing Service Gateway rendezvous owner;
- active-Goal submission uses `transport-correlation:sha256:<64>` correlation rather than device or Node identity as user verification;
- Gateway authority remains `NONE`.

The resident request files and lower-level consumer receipts retain parent/root operation provenance under `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`. That provenance remains correct. Active-Goal correlation is carried by manifest/rendezvous/component composition and the task/COSV/Node/KV evidence chain.

Source merge and CI validation do not prove a resident has received, admitted, or executed either request.

## Current runtime/evidence state

```text
eligible physical device requirement: ANY SUPPORTED STEGOS-CAPABLE DEVICE
established/recovered Node required: YES
physical-device identity gate: PROHIBITED
specific-iPhone requirement: NOT_APPLICABLE
remote connected-device requirement: NOT_APPLICABLE
KV/SKAP-backed operation state: REQUIRED WHEN THE OPERATION REQUIRES USER/SECRET CONTINUITY
RTC-RESIDENT-RENDEZVOUS-010 selected for resident delivery: YES
external-collab rendezvous consumer registration: SOURCE MERGED + VALIDATED
task-bound established-Node execution: NOT OBSERVED
WorkerCoordinator claim/fence for this execution: NOT OBSERVED
Interlock/InTr admission for this execution: NOT OBSERVED
resident reseal consumption receipt: NOT OBSERVED
resident consent-listener consumption receipt: NOT OBSERVED
external-collaboration target custody/readback: NOT PROVEN
```

The unresolved condition is now authentic runtime evidence, not consumer registration or physical-device connectivity.

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

`ONE_CURRENT_DEVICE_END_TO_END_PROVEN` remains superseded for this active Goal because hardware identity is not a completion semantic.

## Next admissible work

Proceed through the existing established-Node runtime path. For an authentic Goal-bound invocation:

1. bind Goal Task `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` and COSV `71000000100110` in the applicable manifest/invocation context;
2. establish or recover an eligible StegVerse Node without treating its physical device identity as verification;
3. bind applicable KV/SKAP continuity for the reseal operation;
4. obtain WorkerCoordinator claim/fence where required and Interlock/InTr admission for the exact governed operation;
5. deliver the exact bounded reseal/listener request through `RTC-RESIDENT-RENDEZVOUS-010`;
6. retain exact resident consumption and rendezvous acknowledgement evidence;
7. advance custody/readback and callback reachability only from authentic resulting evidence.

Do not initiate provider consent before custody and sovereign callback reachability are authentically proven. Do not create device verification, a second user-operated-device requirement, a new scheduler, or a new runtime authority plane.

## README review

No README change is required. This remains a bounded extension and use of an already-canonical reusable transport component; the authority model and public capability description are unchanged.

## Human action

None.
