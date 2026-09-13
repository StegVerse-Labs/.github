# MIR TVC Provider Roundtrip — Reusable Task Component Reconciliation

Updated: 2026-09-12
Goal Task ID: `MIR-TVC-PROVIDER-ROUNDTRIP-001`
COSV: `50000000100000`
Parent: `MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002`
Status: `ACTIVE / IDENTITY PRESERVED / SOURCE VALIDATED / NODE-MIRROR BUILD-TEST LANE BOUND / EXTERNAL ENDPOINT RUNTIME PENDING`

## Reconciliation result

The Goal Task remains valid. No new Goal Task or reusable component is required. The decomposition score is 25, so further bespoke orchestration is prohibited; the remaining work is composed from existing reusable components and canonical owners.

Selected composition:

1. `RT-EXTERNAL-ADAPTER-ESTABLISH-001` — reuse the merged MIR-specific TVC profile/validator as endpoint translation only.
2. `RTC-ROUNDTRIP-003` — reuse the canonical governed request/response cycle. During build/test the far-side counterpart is a StegOS Node instance labeled `MIR NODE MIRROR`; later the authentic MIR endpoint substitutes for that counterpart without changing StegVerse-side choreography.
3. `RTC-INTERLOCK-INTR-TRANSPORT-008` — reuse the existing governed outbound/return transport and receipt path.
4. `TVC-PROVIDER-OPERATION-BROKER-003` — reuse the existing TV/TVC non-exportable provider-operation/session owner for authentic external provider execution where credentials/session are required.
5. `TVC-CAPABILITY-RUNTIME-002` — reuse the existing TVC runtime observer for provider-session/runtime evidence.

`RT-INTR-PROTOCOL-ESTABLISH-001` is not selected because an applicable protocol already exists. Publisher, SDK return assembly, replay/reconstruction, and full evidence-package projection are parent Goal Task stages and are not child component implementations.

## Canonical external-roundtrip build/test binding

The build/test path uses the same canonical external-roundtrip process required for external integrations:

```text
StegVerse initiating component
-> Interlock/InTr
-> external-system StegOS Node Mirror
-> external-system contract behavior
-> return packet
-> Interlock/InTr
-> StegVerse receiving component
```

For this task:

```text
Run-2 bounded history
-> MIR NODE MIRROR
-> MIR-profile historical accounting response
-> existing evaluator-read-review return path
-> SDK:EvaluatorReviewIngress
```

The mirror uses the existing StegOS `SovereignLocalEventRuntimeAdapter` with `EVENT_EPHEMERAL / NOT_REQUIRED` rendezvous and `requires_other_machine=false`. This is a logical far-side test instance, not another physical machine and not another runtime lifecycle.

Authentic MIR later replaces only the far-side counterpart:

```text
MIR NODE MIRROR -> AUTHENTIC MIR
```

while preserving the same StegVerse request, transport, correlation, return, SDK evaluation, replay/reconstruction, and Publisher contracts.

## Evidence classes

A real `MIR NODE MIRROR` execution is authentic runtime evidence for the build/test round trip. It must preserve actual WorkerCoordinator claim/fence evidence, admitted Interlock/InTr transitions, exact packet/receipt bindings, same-device StegOS runtime materialization, return ingress, and downstream SDK evidence. Source or CI cannot satisfy those predicates.

Authentic external MIR execution remains a distinct endpoint-specific evidence class proving that the real external service performed the contracted far-side work. This distinction is endpoint provenance, not a claim that the mirror run is synthetic.

Build/test runtime predicates:

- `MIR_NODE_MIRROR_ROUNDTRIP_EXECUTED`
- `MIR_NODE_MIRROR_RETURN_ADMITTED_TO_SDK`

Authentic external endpoint predicates:

- `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED`
- `AUTHENTIC_MIR_RESULT_RECEIPT_RETAINED`

## Current source truth

Merged TVC PR #415 at `85a42792d5a4e4d081ad7eead4995efbddd4d58d` provides the MIR profile, validator, broker dispatch, tests, dedicated validation lane, and fail-closed policy boundary. Source/CI validation is complete. It does not prove runtime execution.

StegOS issue #364 / PR #365 parameterizes the canonical external-roundtrip build/test pattern as `MIR NODE MIRROR` using the existing same-device `SovereignLocalEventRuntimeAdapter`; no new reusable component or physical-machine dependency is introduced.

Satisfied child source predicates:

- `MIR_PROFILE_REGISTERED_IN_CANONICAL_TVC_PROVIDER_REGISTRY`
- `CANONICAL_PROVIDER_BROKER_DISPATCHES_TO_MIR_VALIDATOR`
- `MIR_STANDING_REQUEST_BOUND_AND_ADMITTED`
- `MIR_SUBMIT_EVENT_FAILS_CLOSED_WITHOUT_VERIFIED_EVENT_MAPPING`
- `MIR_POLICY_EVALUATE_FORBIDDEN`
- `MIR_CREDENTIAL_NOT_EXPORTED`
- `MIR_BODY_AND_LEASE_MUTATION_FAIL_CLOSED`

The event-semantic mapping dependency is conditional, not a blocker for the build/test mirror round trip or the required `READ_STANDING` round trip. `SUBMIT_EVENT` remains fail-closed unless a specific Run-2 transition is proven semantically equivalent to an authoritative MIR event type.

## Authority map

Task Registry coordinates only. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns provider/session authority. MIR owns its external historical-accounting behavior when the authentic endpoint is used. StegVerse owns governance. KV/SKAP Vault remains the sole user-verification authority. Master Records owns observed-reality custody/reconstruction. HeartBeat is observability only. GitHub has no runtime authority.

`MIR NODE MIRROR` receives no new authority; it is the canonical build/test far-side counterpart instance for exercising the MIR contract profile.

## Duplicate orchestration retired/superseded

Do not create a bespoke MIR transport, MIR-specific provider/session broker, parallel TVC runtime observer, task-specific generic round-trip engine, child-task Publisher/SDK/reconstruction chain, or a separate physical host solely to represent the external counterpart during build/test. Reuse the Node Mirror pattern and existing reusable components.

## Next admissible work

1. Finish validating and integrating StegOS PR #365.
2. Execute the MIR NODE MIRROR round trip through the existing same-device StegOS runtime + Interlock/InTr return path and retain authentic mirror runtime/SDK ingress evidence.
3. Continue parent Run-2 delta/replay/reconstruction/Publisher stages from that returned accounting artifact.
4. Later substitute authentic MIR as the far-side endpoint and collect the distinct provider-specific evidence without redesigning the StegVerse side.

Do not infer any runtime predicate from source, CI, merge state, or static compatibility.
