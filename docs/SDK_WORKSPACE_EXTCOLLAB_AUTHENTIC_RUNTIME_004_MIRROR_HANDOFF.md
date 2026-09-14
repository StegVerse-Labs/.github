# SDK WorkSpace External-Collaboration Authentic Runtime 004 Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`
Parent Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV: `71000000100110`
Status: `ACTIVE / RENDEZVOUS CONSUMERS MERGED / GOAL-BOUND SUBMISSION SOURCE ADDED / AUTHENTIC NODE CONSUMPTION REQUIRED`

## Purpose and identity

This is the canonical runtime-evidence handoff for the active Goal Task. Goal identity, COSV, authority separation, reusable-component composition, and evidence-class discipline remain unchanged.

## Device / Node / KV invariant

StegOS-capable physical devices are interchangeable execution/transport surfaces. The Goal is not bound to an iPhone, another device, connector inventory, or persistent device identity. The runtime subject is an established or recovered StegVerse Node; Node identity is routing/runtime-evidence correlation only. KV/SKAP Vault remains the sole user-verification authority and supplies applicable persistent user/secret continuity. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns credential/provider/release authority. Master Records owns observed reality/custody/reconstruction. GitHub and the Service Gateway mint no runtime authority.

The applicable sequence is:

```text
eligible StegOS-capable device
-> establish/recover Node
-> bind applicable KV/SKAP continuity
-> Goal/COSV-bound rendezvous submission
-> WorkerCoordinator claim/fence and Interlock/InTr admission where required
-> exact bounded resident operation
-> authentic receipts / acknowledgement
-> custody, callback and later provider stages only when predicates permit
```

## Reusable rendezvous source state

`RTC-RESIDENT-RENDEZVOUS-010` is selected only for `resident_client_secret_reseal` and `resident_consent_listener`.

Resident-side consumer admission is merged through `.github` PR #1756 at `8770a4007e72f7d407b37b9675916d2121c7c1b2`; Organization Control `34779449112`, Deterministic Repository Suite `34779449080`, and Heartbeat Worker Project `34779449072` passed. Service Gateway admission is merged through `StegVerse-org/LLM-adapter` PR #337 at `ded63a597140a27f39469b77f8ad0e04b1fc4eef`; Work Mutation Safety `34779030889` and validation `34779030902` passed.

The two exact existing inner request contracts remain authoritative. Reseal terminal success is `COMPLETED` or `TARGET_ALREADY_PRESENT`; listener terminal success is `COMPLETED` or `SERVICE_ALREADY_HEALTHY`; `BLOCKED` remains fail-closed. Node identity remains routing/correlation only and Gateway execution authority remains `NONE`.

## Goal-bound request-submission binding

Fresh source inspection after the consumer merges found the first missing transition: the Gateway exposes discovery/request storage and the Node-side component advertises/fetches, but no source caller bound this active Goal/COSV to a stored rendezvous request.

This change adds:

- `control/resident-rendezvous-invocation.d/sdk-workspace-extcollab-authentic-runtime-004.json`
- `scripts/submit_sdk_workspace_extcollab_resident_rendezvous.py`

The invocation binding admits exactly the two existing consumers and preserves physical-device identity gate `NONE_PROHIBITED`, Node routing/correlation-only semantics, KV/SKAP user-verification exclusivity, WorkerCoordinator claim/fence authority, InTr transition authority, and TV/TVC credential authority.

The submitter:

1. loads and validates the exact Goal/COSV invocation binding;
2. loads the exact immutable resident request for one admitted consumer;
3. asks the existing Service Gateway rendezvous discovery surface for one currently advertised established Node for that consumer;
4. creates a `transport-correlation:sha256:<64>` reference over Goal ID, COSV, component, consumer, Node routing ref, request digest, invocation-manifest digest and submission time;
5. POSTs the existing bounded request to the existing rendezvous request endpoint;
6. records only `REQUEST_STORED_PENDING_RESIDENT_CONSUMPTION` when the Gateway returns `PENDING` with execution authority `NONE`.

A submission receipt explicitly records WorkerCoordinator claim/fence, InTr admission, resident execution, and provider contact as **not observed**. Therefore source construction or successful request storage cannot upgrade runtime evidence.

## Reusable ECE lifecycle applicability correction

The Goal record historically carried three predicates originating from `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001`:

- `AUTHENTIC_POST_MERGE_RESIDENT_LIFECYCLE_INVOCATION_OBSERVED`
- `SAME_INVOCATION_REUSABLE_LIFECYCLE_CHAIN_PROVEN`
- `UTC_HOUR_SLOT_SATISFACTION_WITHOUT_DUPLICATE_EXECUTION_PROVEN`

Current reusable-task source defines `RT-ECOSYSTEM-CONTINUITY-EVALUATION-001` as the periodic **Ecosystem Continuity Evaluation** cycle: evaluate already-materialized ecosystem observations, retain ECE evidence through Master Records, prepare Healer findings, and project Site-safe ECE output. No source binds the external-collaboration reseal/listener operations to that ECE invocation or its hourly scheduler semantics.

Those three ECE lifecycle/hour-slot predicates are therefore **not active completion predicates for this Goal**. They remain historical provenance in older records until the canonical task-record projection is compacted; they must not block reseal/listener progression and must not be used as substitute runtime evidence.

## Current runtime/evidence state

```text
eligible physical device: ANY SUPPORTED STEGOS-CAPABLE DEVICE
established/recovered Node required: YES
physical-device identity gate: PROHIBITED
KV/SKAP continuity: REQUIRED WHEN OPERATION REQUIRES USER/SECRET STATE
RTC-RESIDENT-RENDEZVOUS-010 consumer source: MERGED + VALIDATED
Goal/COSV-bound submission source: PRESENT IN CURRENT CHANGE SET
rendezvous request submission: NOT AUTHENTICALLY OBSERVED
rendezvous acknowledgement: NOT AUTHENTICALLY OBSERVED
WorkerCoordinator claim/fence for this work: NOT OBSERVED
Interlock/InTr admission for this work: NOT OBSERVED
resident reseal consumption: NOT OBSERVED
resident consent-listener consumption: NOT OBSERVED
external-collaboration target custody/readback: NOT PROVEN
```

## Active remaining Goal predicates

- `RENDEZVOUS_REQUEST_SUBMISSION_OBSERVED`
- `RENDEZVOUS_REQUEST_ACKNOWLEDGEMENT_OBSERVED`
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

`ONE_CURRENT_DEVICE_END_TO_END_PROVEN` remains superseded because hardware identity is not a completion semantic.

## Next admissible work

After this submitter source is merged and validated, use the existing Goal/COSV binding to store the exact reseal request for an advertised established Node. Request storage is only transport state. The Node must independently satisfy applicable KV/SKAP continuity, WorkerCoordinator claim/fence, and Interlock/InTr admission before the operation can produce authentic resident evidence. Preserve the resulting request-store, resident-consumption, rendezvous-acknowledgement, and custody receipts as separate evidence predicates.

Only after authentic target custody/readback and sovereign callback reachability are proven may owner-present Google consent proceed. Do not create device verification, a second user-operated-device requirement, a new scheduler, a new Gateway, or another runtime authority plane.

## README review

No README change is required. This is a bounded Goal-specific invocation binding over an already-documented reusable rendezvous component; public capability and authority semantics do not change.

## Human action

None.
