# MIR TVC Provider Roundtrip — Reusable Task Component Reconciliation

Updated: 2026-09-12
Goal Task ID: `MIR-TVC-PROVIDER-ROUNDTRIP-001`
COSV: `50000000100000`
Parent: `MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002`
Status: `ACTIVE / IDENTITY PRESERVED / SOURCE VALIDATED / RUNTIME PENDING`

## Reconciliation result

The Goal Task remains valid. No new Goal Task or reusable component is required. The decomposition score is 25, so further bespoke orchestration is prohibited; the remaining work is composed from existing reusable components and canonical owners.

Selected composition:

1. `RT-EXTERNAL-ADAPTER-ESTABLISH-001` — reuse the merged MIR-specific TVC profile/validator as endpoint translation only.
2. `RTC-ROUNDTRIP-003` — one required `READ_STANDING` provider round trip; `SUBMIT_EVENT` is a conditional second occurrence only if exact Run-2 semantics match the authoritative MIR event vocabulary.
3. `RTC-INTERLOCK-INTR-TRANSPORT-008` — reuse the existing external-provider-operation governed transport/admission path.
4. `TVC-PROVIDER-OPERATION-BROKER-003` — reuse the existing TV/TVC non-exportable provider-operation/session owner.
5. `TVC-CAPABILITY-RUNTIME-002` — reuse the existing TVC runtime observer for authentic runtime evidence.

`RT-INTR-PROTOCOL-ESTABLISH-001` is not selected because an applicable protocol already exists. Publisher, SDK return assembly, replay/reconstruction, and full evidence-package projection are parent Goal Task stages and are not completion predicates of this child Goal Task.

## Current source truth

Merged TVC PR #415 at `85a42792d5a4e4d081ad7eead4995efbddd4d58d` provides the MIR profile, validator, broker dispatch, tests, dedicated validation lane, and fail-closed policy boundary. Source/CI validation is complete. It does not prove runtime execution.

Satisfied child predicates:

- `MIR_PROFILE_REGISTERED_IN_CANONICAL_TVC_PROVIDER_REGISTRY`
- `CANONICAL_PROVIDER_BROKER_DISPATCHES_TO_MIR_VALIDATOR`
- `MIR_STANDING_REQUEST_BOUND_AND_ADMITTED`
- `MIR_SUBMIT_EVENT_FAILS_CLOSED_WITHOUT_VERIFIED_EVENT_MAPPING`
- `MIR_POLICY_EVALUATE_FORBIDDEN`
- `MIR_CREDENTIAL_NOT_EXPORTED`
- `MIR_BODY_AND_LEASE_MUTATION_FAIL_CLOSED`

Remaining child predicates:

- `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED`
- `AUTHENTIC_MIR_RESULT_RECEIPT_RETAINED`

The event-semantic mapping dependency is conditional, not a blocker for the required `READ_STANDING` round trip. `SUBMIT_EVENT` remains fail-closed unless a specific Run-2 transition is proven semantically equivalent to an authoritative MIR event type.

## Authority map

Task Registry coordinates only. WorkerCoordinator owns claim/fence. Interlock/InTr owns governed transition/admission. TV/TVC owns provider/session authority. MIR owns historical accounting. StegVerse owns governance. KV/SKAP Vault remains the sole user-verification authority. Master Records owns observed-reality custody/reconstruction. HeartBeat is observability only. GitHub has no runtime authority.

No device-local user verification is introduced.

## Duplicate orchestration retired/superseded

Do not create a bespoke MIR transport, MIR-specific provider/session broker, parallel TVC runtime observer, task-specific generic round-trip engine, or child-task Publisher/SDK/reconstruction chain. Preserve the merged MIR translator as task-specific configuration of the reusable adapter component; preserve all historical evidence.

## Next admissible work

Use the existing TV/TVC runtime/session owner and existing InTr path to attempt the required `READ_STANDING` round trip. Record the authentic provider result/use receipt or exact failure. Do not infer success from source, CI, merge state, or static compatibility. If the provider session is absent, that absence is the runtime result to remediate and re-observe.
