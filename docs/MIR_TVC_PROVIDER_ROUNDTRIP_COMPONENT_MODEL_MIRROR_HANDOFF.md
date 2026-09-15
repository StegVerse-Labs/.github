# MIR TVC Provider Roundtrip — Reusable Task Component Reconciliation

Updated: 2026-09-15
Goal Task ID: `MIR-TVC-PROVIDER-ROUNDTRIP-001`
COSV: `50000000100000`
Parent: `MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002`
Status: `ACTIVE / CHECKED_OUT / REUSABLE INTR DECOMPOSITION SOURCE-VALIDATED / BUILD-TEST RUNTIME EVIDENCE STILL PENDING / AUTHENTIC MIR ENDPOINT PENDING`

## Reconciliation result

The Goal Task identity and COSV remain unchanged. No new Goal Task or reusable component is required.

The MIR Node Mirror now uses the four reusable Interlock/InTr task identities as the default protocol decomposition:

1. `RT-INTR-BOUNDARY-ADMISSION-001` — bind and validate the exact manifest/envelope, payload integrity, destination, operation, and applicable standing before transition.
2. `RT-INTR-GOVERNED-TRANSITION-001` — evaluate the admitted transition under applicable Transition Elements while keeping execution separate from authority effect.
3. `RT-INTR-ROUNDTRIP-CORRELATION-001` — preserve request/response correlation, destination binding, exactly-once/replay semantics, manifest continuity, and transport/application-result separation.
4. `RT-INTR-EVIDENCE-CUSTODY-001` — bind receipt-chain and artifact hashes and hand evidence to Master Records custody/reconstruction without giving custody transition authority.

`RT-INTR-PROTOCOL-ESTABLISH-001` remains the protocol-definition root but is not invoked for this MIR flow because an applicable Interlock/InTr protocol already exists.

## Implementation components retained

The reusable RT-INTR identities are protocol decomposition. They do not replace the existing implementation components:

- `RT-EXTERNAL-ADAPTER-ESTABLISH-001` — MIR endpoint/profile translation only.
- `RTC-ROUNDTRIP-003` — governed request/response lifecycle implementation.
- `RTC-INTERLOCK-INTR-TRANSPORT-008` — governed packet movement and transport receipts.
- `TVC-PROVIDER-OPERATION-BROKER-003` — TV/TVC provider-operation/session owner for authentic external provider execution.
- `TVC-CAPABILITY-RUNTIME-002` — provider-session/runtime observation.
- `SovereignLocalEventRuntimeAdapter` — bounded same-device EVENT_EPHEMERAL MIR Node Mirror execution substrate.

No bespoke MIR transport, second provider broker, second runtime lifecycle, parallel InTr authority, or second user-operated machine is introduced.

## Canonical MIR Node Mirror source/test validation

StegOS PR `#393` validated the MIR Node Mirror against this reusable decomposition at exact head:

```text
validated head: a29ed2dbc904e2c6648fe6a7cecf9a29351a2ef8
StegOS CI run: 35001112081
result: SUCCESS
full suite: 1649 passed
MIR external-roundtrip execution test: PASS
merge SHA: 8ade8168e44b3b54bd3f24edfcc047397512a356
```

The external-roundtrip test exercises the existing canonical runtime lane and verifies:

- exact MIR Run-2 manifest/hash binding;
- `EXTERNAL_FRAMEWORK_INGRESS` receipt generation;
- request/response correlation preservation;
- original outbound manifest continuity;
- bounded EVENT_EPHEMERAL mirror execution;
- linked request/response receipt chain;
- exact return-packet retention with hash and correlation binding;
- evidence retention before lease release;
- terminal lease closure;
- `authority_effect=NONE`;
- `requires_other_machine=false`.

This is source/test validation of the reusable decomposition and implementation contract. GitHub Actions has no runtime authority and the CI result is not promoted to authentic MIR Node Mirror runtime evidence.

## Canonical external-roundtrip build/test binding

```text
StegVerse initiating component
-> RT-INTR-BOUNDARY-ADMISSION-001
-> RT-INTR-GOVERNED-TRANSITION-001
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> MIR NODE MIRROR
-> MIR-profile behavior
-> RT-INTR-ROUNDTRIP-CORRELATION-001
-> governed Interlock/InTr return
-> StegVerse receiving component
-> RT-INTR-EVIDENCE-CUSTODY-001
```

For this task:

```text
Run-2 bounded history
-> MIR NODE MIRROR
-> MIR-profile historical accounting response
-> existing evaluator-read-review return path
-> SDK:EvaluatorReviewIngress
```

Authentic MIR later replaces only the far-side counterpart:

```text
MIR NODE MIRROR -> AUTHENTIC MIR
```

The StegVerse-side admission, governed transition, transport, correlation, return, SDK evaluation, replay/reconstruction, evidence, and Publisher contracts remain unchanged.

## Evidence classes

Source/test validation now proves that the reusable RT-INTR decomposition is correctly represented by the MIR Node Mirror implementation and tests.

Build/test runtime predicates remain unsatisfied until authentic MIR Node Mirror execution produces retained runtime/Interlock/InTr/SDK evidence:

- `MIR_NODE_MIRROR_ROUNDTRIP_EXECUTED`
- `MIR_NODE_MIRROR_RETURN_ADMITTED_TO_SDK`

Authentic external endpoint predicates remain separately required:

- `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED`
- `AUTHENTIC_MIR_RESULT_RECEIPT_RETAINED`

No source, merge, CI, or mirror result may substitute for authentic external MIR endpoint evidence.

## Authority map

Task Registry coordinates only. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns provider/session authority. MIR owns external MIR behavior when the authentic endpoint is used. StegVerse owns governance. KV/SKAP Vault is sole user-verification authority. Master Records owns observed-reality custody/reconstruction. HeartBeat is observability only. GitHub has no runtime authority.

The MIR Node Mirror receives no governance, transition, credential, provider, user-verification, or external-MIR authority.

## Default reuse rule derived from this validation

For future governed connections, select only the reusable InTr tasks actually required by the exchange. Use the existing normalized protocol whenever it represents the endpoint without ambiguity. Derive an endpoint-specific adapter only for endpoint translation that cannot be represented by the normalized protocol; never move endpoint semantics into the governance boundary merely because an adapter is needed.

## Next admissible work

1. Validate and merge this canonical `.github` reconciliation at exact head.
2. Execute the MIR Node Mirror through the authentic same-device canonical runtime path and retain Interlock/InTr plus SDK return evidence.
3. Reconcile the two build/test runtime predicates only from that retained runtime evidence.
4. Later substitute authentic MIR as the far-side endpoint and satisfy the distinct provider-specific predicates without redesigning the StegVerse side.
