# MIR TVC Provider Roundtrip — Reusable Task Component Reconciliation

Updated: 2026-09-15
Goal Task ID: `MIR-TVC-PROVIDER-ROUNDTRIP-001`
COSV: `50000000100000`
Parent: `MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002`
Status: `ACTIVE / CHECKED_OUT / REUSABLE INTR PROMOTED / MIR NODE MIRROR BUILD-TEST SATISFIED / AUTHENTIC MIR RESULT SATISFIED / TVC MIR PROVIDER SESSION PENDING`

## Canonical reusable protocol decomposition

The MIR flow uses the existing applicable Interlock/InTr protocol and the following reusable task identities:

1. `RT-INTR-BOUNDARY-ADMISSION-001`
2. `RT-INTR-GOVERNED-TRANSITION-001`
3. `RT-INTR-ROUNDTRIP-CORRELATION-001`
4. `RT-INTR-EVIDENCE-CUSTODY-001`

Lifecycle projection: `data/reusable-task-lifecycle-projections/MIR-TVC-PROVIDER-ROUNDTRIP-001.json`.

The four RT-INTR identities are `PROMOTED_VALIDATED_REUSABLE` on the additive registry-shard surface and are not duplicated into `data/reusable-task-registry.json`.

`RT-INTR-PROTOCOL-ESTABLISH-001` remains the definition root but is not invoked because an applicable protocol already exists.

The reusable RT-INTR tasks do not replace the implementation components:

- `RT-EXTERNAL-ADAPTER-ESTABLISH-001`
- `RTC-ROUNDTRIP-003`
- `RTC-INTERLOCK-INTR-TRANSPORT-008`
- `TVC-PROVIDER-OPERATION-BROKER-003`
- `TVC-CAPABILITY-RUNTIME-002`
- `SovereignLocalEventRuntimeAdapter`

No duplicate MIR transport, runtime lifecycle, provider broker, WorkerCoordinator, InTr authority, credential path, or second device is introduced.

## Predicate reconciliation

Satisfied:

- `MIR_NODE_MIRROR_ROUNDTRIP_EXECUTED`
- `MIR_NODE_MIRROR_RETURN_ADMITTED_TO_SDK`
- `AUTHENTIC_MIR_RESULT_RECEIPT_RETAINED`

Pending:

- `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED`

## MIR live standing boundary

The frozen `POST /v1/policy/standing` shape remains valid only for source/fixture validation. Canonical TVC live forwarding is fail-closed until authoritative MIR partner material confirms the exact standing endpoint, path, and method contract.

`/v1/policy/evaluate` remains forbidden. `SUBMIT_EVENT` remains fail-closed until a semantics-valid MIR event mapping is proven.

## Authority map

Task Registry coordinates work only. WorkerCoordinator owns claim/fence where applicable. Interlock/InTr owns governed transition/admission. TV/TVC owns provider/session and credential authority. MIR owns authentic external MIR behavior. StegVerse owns governance. KV/SKAP Vault owns user verification. Master Records owns observed-reality custody/reconstruction. GitHub has no runtime authority.

## Next admissible work

Continue only the existing `TVC-CAPABILITY-RUNTIME-002` observer lane. Promote `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED` only from a retained authentic `READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND` receipt proving the relevant TV/TVC vault-backed session. Replace the standing live gate only after authoritative MIR partner-contract confirmation.
