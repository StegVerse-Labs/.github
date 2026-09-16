# MIR TVC Provider Roundtrip — Reusable Task Component Reconciliation

Updated: 2026-09-16
Goal Task ID: `MIR-TVC-PROVIDER-ROUNDTRIP-001`
COSV: `50000000100000`
Parent: `MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002`
Status: `ACTIVE / CHECKED_OUT / REUSABLE INTR PROMOTED / MIR NODE MIRROR BUILD-TEST SATISFIED / AUTHENTIC MIR RESULT SATISFIED / TVC MIR PROVIDER SESSION PENDING`

## Canonical reusable protocol decomposition

The MIR flow uses the existing applicable Interlock/InTr protocol identities:

1. `RT-INTR-BOUNDARY-ADMISSION-001`
2. `RT-INTR-GOVERNED-TRANSITION-001`
3. `RT-INTR-ROUNDTRIP-CORRELATION-001`
4. `RT-INTR-EVIDENCE-CUSTODY-001`

The goal also selects the existing provider/runtime identities:

- `RT-TVC-PROVIDER-OPERATION-BROKER-001`
- `RT-TVC-PRIMARY-RUNTIME-BINDING-001`
- `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001`
- `RTC-ROUNDTRIP-003`
- `RTC-INTERLOCK-INTR-TRANSPORT-008`
- `TVC-PROVIDER-OPERATION-BROKER-003`
- `TVC-PRIMARY-RUNTIME-BINDER-005`
- `TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006`
- `TVC-CAPABILITY-RUNTIME-002`

No duplicate MIR transport, runtime lifecycle, provider broker, WorkerCoordinator, InTr authority, credential path, listener, host, or second device is introduced.

## Predicate reconciliation

Satisfied:

- `MIR_NODE_MIRROR_ROUNDTRIP_EXECUTED`
- `MIR_NODE_MIRROR_RETURN_ADMITTED_TO_SDK`
- `AUTHENTIC_MIR_RESULT_RECEIPT_RETAINED`

Pending:

- `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED`

The task remains `ACTIVE / CHECKED_OUT`. Source/CI changes cannot satisfy the pending authentic provider-session predicate.

## Authority map

Task Registry coordinates work only. WorkerCoordinator owns claim/fence where applicable. Interlock/InTr owns governed transition/admission. TV/TVC owns provider/session and credential authority. MIR owns authentic external MIR behavior. StegVerse owns governance. KV/SKAP Vault owns user verification. Master Records owns observed-reality custody/reconstruction. GitHub has no runtime authority.

## No permanently connected-device prerequisite

A continuously connected user-operated or remote device is not a prerequisite for this goal. The reusable-task construct is `TRIGGER_ONCE_ADVANCE_UNTIL_COMPLETION_OR_REAL_BOUNDARY`, requires no manual coordination between machine-admissible internal steps, and materializes ephemeral runners where possible from existing execution surfaces. Durable identity, receipts, and Master Records evidence survive runner expiry.

PR #2010 corrected the earlier connector-availability continuation model and merged as `aef1f14140f3aff6109745156fd1baa189019787` after exact-head validation. Future continuation must never wait for a device to remain connected merely to be available for work.

## Standing provider operation

The existing standing request remains:

```text
control/resident-execution-request.d/mir-tvc-provider-roundtrip-001.json
provider_request_id: MIR-RUN2-EVENT-001
provider_operation: SUBMIT_EVENT
receipt_ref: receipts/mir-tvc-provider-roundtrip/MIR-RUN2-EVENT-001.latest.json
```

Only this already-standing request may be consumed. A fresh WorkerCoordinator claim/fence is required for a new execution attempt. The TVC non-exportable broker remains the only credential-use path.

## 2026-09-16 reusable execution-binding audit

Review of the registered reusable path exposed three source defects after the connected-device correction:

1. `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001` declared a cross-repository runner reference (`StegVerse-Labs/TVC:scripts/observe_tvc_runtime_boundary.py`) while `scripts/trigger_reusable_task.py` admits only local `scripts/*.py` runners. The reusable invocation therefore could not materialize its declared runner.
2. The reusable observation identity declared Interlock/InTr admission and Master Records custody/reconstruction as runner completion predicates even though the generic trigger validates runner completion before performing Master Records. That made the lifecycle circular.
3. The generic reusable trigger carries a validated runner result to Master Records but does not itself implement `RT-INTR-BOUNDARY-ADMISSION-001`. Therefore the MIR provider transaction must retain authentic canonical InTr request/response receipts before the reusable observation runner may report `INTERLOCK_INTR_RECEIPT_ADMITTED`.

The canonical StegOS registry already contains the correct provider-generic transport profile:

```text
profile_id: external-provider-operation
request_class: EXTERNAL_PROVIDER_OPERATION
payload_schema: stegverse.external-provider.operation-request/v1
operation: REQUEST_PROVIDER_OPERATION
source: STEGOS_ECOSYSTEM / LLMAdapter:ProviderOperationClient
destination: STEGOS_ECOSYSTEM / TVC:ProviderOperationBroker
response: reverse path
authorization_required: true
credential_authority: TV/TVC
authority_effect: NONE
```

The StegOS profile handoff explicitly requires a resident WorkerCoordinator consumer to construct the request packet, retain the real ingress receipt, execute only after the separate TVC provider lease/boundary is valid, then construct and retain the response packet/receipt. No MIR-specific InTr profile is required.

## Current source repair

Branch `fix-mir-reusable-trigger-execution-20260916` now implements the bounded repair:

- `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001` uses local runner `scripts/reconcile_tvc_runtime_boundary_reusable.py`;
- runner completion requires qualifying real provider evidence, READY derivation, and canonical InTr request/response evidence; Master Records remains post-run lifecycle work;
- the checked-in MIR reusable invocation binds `provider_operation_receipt_ref=receipts/mir-tvc-provider-roundtrip/MIR-RUN2-EVENT-001.latest.json` and is deterministically constructor-checked;
- `workers/mir_tvc_provider_roundtrip_worker.py` uses the already-local StegOS `CanonicalInTrConnector(profile=external-provider-operation)` around the same exact TVC broker transaction;
- TVC validates the exact MIR provider profile/lease/live-operation boundary before the provider call;
- the exact provider result and `use_receipt` are retained before response-transport continuation;
- a completed provider consequence is reused for downstream reconciliation and must not be blindly executed again if InTr/Master Records continuation later fails;
- an indeterminate broker outcome is retained as `FAIL_CLOSED_PROVIDER_OPERATION_OUTCOME_UNKNOWN` with provider retry prohibited until the existing transaction outcome is reconciled;
- after a complete request/result InTr chain exists, the worker invokes only the registered reusable trigger for same-transaction observation and Master Records custody/reconstruction.

Focused regression coverage:

```text
tests/test_mir_tvc_provider_roundtrip_worker.py
tests/test_mir_tvc_reusable_runtime_reconciliation.py
```

Audit evidence: `reports/reusable-task-validation/MIR-TVC-PROVIDER-ROUNDTRIP-001-execution-binding-audit-20260916.json`.

## Completion boundary

The goal may retire only when one authentic same transaction proves all of the following:

```text
fresh WorkerCoordinator claim/fence
MIR-RUN2-EVENT-001 exact request
canonical external-provider-operation InTr request chain complete
TVC non-exportable broker ALLOW_OPERATION_RESULT
exact TV/TVC use_receipt retained
canonical external-provider-operation InTr response chain complete
READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND derived
reusable runner completion evidence validated
Master Records custody accepted
Master Records exact reconstruction confirmed
AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED satisfied
```

A source merge, green CI, diagnostic observer result, GitHub receipt, or unavailable connector cannot substitute for this evidence.

## Next admissible work

Validate the source repair on exact head. If green, merge with expected-head protection. Then allow the existing standing WorkerCoordinator request to consume `MIR-RUN2-EVENT-001` through the repaired on-demand path. Accept either the authentic same-transaction completion chain above or the exact fail-closed runtime boundary produced by the repaired worker. Do not create or wait for a persistent device, runtime, scheduler, broker, credential path, listener, host, or second-device dependency. Retire only after the authentic provider-session predicate and all canonical completion conditions are satisfied.
