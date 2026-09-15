# MIR TVC Provider Roundtrip — Reusable Task Component Reconciliation

Updated: 2026-09-15
Goal Task ID: `MIR-TVC-PROVIDER-ROUNDTRIP-001`
COSV: `50000000100000`
Parent: `MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002`
Status: `ACTIVE / CHECKED_OUT / REUSABLE INTR DECOMPOSITION CANONICAL / MIR NODE MIRROR BUILD-TEST ROUNDTRIP + SDK RETURN ADMISSION SATISFIED / AUTHENTIC MIR ENDPOINT PENDING`

## Canonical reusable protocol decomposition

The MIR flow uses the existing applicable Interlock/InTr protocol and the following reusable task identities:

1. `RT-INTR-BOUNDARY-ADMISSION-001`
2. `RT-INTR-GOVERNED-TRANSITION-001`
3. `RT-INTR-ROUNDTRIP-CORRELATION-001`
4. `RT-INTR-EVIDENCE-CUSTODY-001`

`RT-INTR-PROTOCOL-ESTABLISH-001` remains the definition root but is not invoked because an applicable protocol already exists.

The reusable RT-INTR tasks classify the already-existing protocol behaviors. They do not replace the implementation components:

- `RT-EXTERNAL-ADAPTER-ESTABLISH-001`
- `RTC-ROUNDTRIP-003`
- `RTC-INTERLOCK-INTR-TRANSPORT-008`
- `TVC-PROVIDER-OPERATION-BROKER-003`
- `TVC-CAPABILITY-RUNTIME-002`
- `SovereignLocalEventRuntimeAdapter`

No duplicate MIR transport, runtime lifecycle, provider broker, WorkerCoordinator, InTr authority, credential path, or second device is introduced.

## Runtime-truth reconciliation

The canonical Site MIR round-trip handoff already records the following executed transitions under `MIR NODE MIRROR` build/test provenance:

```text
MIR-profile request construction: executed/implemented
EVENT_EPHEMERAL lease state-machine execution: executed
canonical runtime request InTr hop transition: executed
MIR NODE MIRROR bounded processing transition: executed
EXTERNAL_FRAMEWORK_INGRESS transition/receipt: executed
canonical runtime response InTr hop transition: executed
return queue / local evidence / closure retention: executed
StegOS exact return packet retention: executed
Site retained exact return packet consumption: executed
Site Universal InTr return admission: executed
STEGVERSE_RETURN_EXIT: executed
SDK:EvaluatorReviewIngress admission: executed
Node EXTERNAL_COUNTERPART_RETURN_ADMITTED transition: executed
```

Canonical source: `StegVerse-Labs/Site/docs/MIR_CONNECTION_ROUNDTRIP_TECHNICAL_GUIDE_MIRROR_HANDOFF.md`.

These transitions predate registration of the four RT-INTR reusable task names, but the new reusable tasks were derived from those exact admission, governed-transition, correlation, and custody behaviors. Therefore the correct action is to reconcile the retained transitions to the reusable decomposition, not to create a second MIR Node Mirror invocation solely to reproduce already-observed state.

## Reusable-task validation

StegOS PR `#393` bound the same MIR runtime implementation to the four RT-INTR identities and passed exact-head CI:

```text
validated head: a29ed2dbc904e2c6648fe6a7cecf9a29351a2ef8
StegOS CI run: 35001112081
result: SUCCESS
full suite: 1649 passed
MIR external-roundtrip execution test: PASS
merge SHA: 8ade8168e44b3b54bd3f24edfcc047397512a356
```

CI establishes implementation/decomposition conformance only. The two runtime predicates below are satisfied from retained canonical MIR build-test transition truth recorded by the Site handoff, not from GitHub Actions.

## Predicate reconciliation

Satisfied from MIR Node Mirror build/test runtime provenance:

- `MIR_NODE_MIRROR_ROUNDTRIP_EXECUTED`
- `MIR_NODE_MIRROR_RETURN_ADMITTED_TO_SDK`

Still pending and not substituted by mirror evidence:

- `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED`
- `AUTHENTIC_MIR_RESULT_RECEIPT_RETAINED`

Authentic MIR later replaces only the far-side counterpart. The StegVerse admission, InTr transition, correlation, return, custody, SDK, reconstruction, and Publisher choreography remain unchanged.

## Authority map

Task Registry coordinates work only. WorkerCoordinator owns claim/fence where applicable. Interlock/InTr owns governed transition/admission. TV/TVC owns provider/session and credential authority. MIR owns authentic external MIR behavior. StegVerse owns governance. KV/SKAP Vault owns user verification. Master Records owns observed-reality custody/reconstruction. GitHub has no runtime authority. MIR NODE MIRROR has `authority_effect=NONE` outside its bounded build/test counterpart role.

## Next admissible work

Continue only the authentic external-endpoint lane when appropriate: substitute authentic MIR as the far-side endpoint using the unchanged protocol, retain TVC/MIR provider-session and MIR result evidence, and do not regress or re-run the already-satisfied mirror predicates unless a later validation specifically requires a fresh execution epoch.
