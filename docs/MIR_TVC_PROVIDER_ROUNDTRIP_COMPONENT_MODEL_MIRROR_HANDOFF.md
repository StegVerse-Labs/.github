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

## Current source repair

Branch `fix-mir-reusable-trigger-execution-20260916` now implements the bounded repair:

- `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001` uses local runner `scripts/reconcile_tvc_runtime_boundary_reusable.py`;
- runner completion requires qualifying real provider evidence, READY derivation, and canonical InTr request/response evidence; Master Records remains post-run lifecycle work;
- the checked-in MIR reusable invocation binds `provider_operation_receipt_ref=receipts/mir-tvc-provider-roundtrip/MIR-RUN2-EVENT-001.latest.json` and is deterministically constructor-checked;
- `workers/mir_tvc_provider_roundtrip_worker.py` uses the already-local generic `RTC-INTERLOCK-INTR-TRANSPORT-008` implementation in `StegOS/stegos/universal_intr_transport.py`, with exact request identity `StegVerse-org/StegVerse-SDK -> TVC:ProviderOperationBroker` and the exact reverse return identity;
- TVC validates the exact MIR provider profile/lease/live-operation boundary before the provider call;
- the exact provider result and `use_receipt` are retained before response-transport continuation;
- a completed provider consequence is reused for downstream reconciliation and must not be blindly executed again if InTr/Master Records continuation later fails;
- an indeterminate broker outcome is retained as `FAIL_CLOSED_PROVIDER_OPERATION_OUTCOME_UNKNOWN` with provider retry prohibited until the existing transaction outcome is reconciled;
- after a complete request/result Universal InTr transport chain exists, the worker invokes only the registered reusable trigger for same-transaction pre-admission reconciliation;
- transport receipts do not satisfy `RT-INTR-BOUNDARY-ADMISSION-001` and grant no admission authority;
- if an authentic explicit Interlock/InTr admission receipt is absent, `scripts/trigger_reusable_task.py` records `INTERLOCK_INTR_ADMISSION_REQUIRED` and stops before Master Records;
- only after explicit Interlock/InTr admission evidence exists may the reusable lifecycle continue to Master Records custody/reconstruction.

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
canonical `RTC-INTERLOCK-INTR-TRANSPORT-008` request transport chain complete
TVC non-exportable broker ALLOW_OPERATION_RESULT
exact TV/TVC use_receipt retained
canonical `RTC-INTERLOCK-INTR-TRANSPORT-008` response transport chain complete
READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND derived
reusable pre-admission runner evidence validated
explicit Interlock/InTr admission receipt retained
Master Records custody accepted
Master Records exact reconstruction confirmed
AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED satisfied
```

A source merge, green CI, diagnostic observer result, GitHub receipt, or unavailable connector cannot substitute for this evidence.

## 2026-09-21 caller-identity and admission-order correction

PR #2018 review established that the existing StegOS `external-provider-operation` connector profile is source-bound to `LLMAdapter:ProviderOperationClient`; MIR Run-2 is canonically owned by `StegVerse-org/StegVerse-SDK`. Reusing that profile would create transport evidence with the wrong caller identity.

The repaired path therefore reuses the existing generic `RTC-INTERLOCK-INTR-TRANSPORT-008` implementation directly:

```text
StegVerse-org/StegVerse-SDK
-> Universal InTr request transport
-> TVC:ProviderOperationBroker
-> existing TVC non-exportable MIR provider operation
-> Universal InTr response transport
-> StegVerse-org/StegVerse-SDK
```

This is transport only. An InTr hop receipt is not an Interlock admission decision. `RT-INTR-BOUNDARY-ADMISSION-001` separately requires exact boundary identity, payload/envelope integrity, applicable standing evaluation, explicit ALLOW/DENY disposition, and a retained admission receipt.

Accordingly, the reusable trigger must stop at `INTERLOCK_INTR_ADMISSION_REQUIRED` before constructing or submitting any Master Records custody request whenever authentic explicit admission evidence is absent. Retrying that continuation must reuse any already-retained provider result and must not repeat the provider consequence.

## Next admissible work

Validate PR #2018 on its exact final head. If all required exact-head lanes are green, merge with expected-head protection. Then allow the already-standing `MIR-RUN2-EVENT-001` WorkerCoordinator request to advance on demand through the repaired path. It may reach authentic provider execution plus canonical transport and then stop at the explicit Interlock admission boundary; it may continue to Master Records only when authentic admission evidence is present. Do not create or wait for a persistent device, runtime, scheduler, broker, credential path, listener, host, or second-device dependency. Retire only after `AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED` and every canonical completion condition are authentically satisfied.
