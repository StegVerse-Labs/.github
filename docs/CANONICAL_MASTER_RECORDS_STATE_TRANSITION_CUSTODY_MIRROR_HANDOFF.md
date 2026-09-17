# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / INVENTORY COMPLETE / CANONICAL CUSTODY API MATERIALIZED / MIR SOURCE ADOPTED / AUTHENTIC RUNTIME SEQUENCE PENDING`

## Canonical rule

Master Records custody/reconstruction is an intrinsic consequence of governed state transition, not a MIR test mechanism.

```text
current governance decision
-> transition occurs, denies, partially completes, or fails closed
-> canonical state-transition receipt is retained
-> exact receipt is submitted to Master Records
-> Master Records retains and reconstructs it
-> only then may the next machine-owned governed transition advance
```

Interlock/InTr remains transition authority. TV/TVC remains credential authority where required. Master Records is custody/reconstruction only and cannot create, admit, authorize, infer, or repair a missing transition.

## Inventory completed

Canonical inventory: `reports/canonical-master-records-state-transition-custody-inventory-20260917.json`.

Key findings:

- `master-records/orchestration/services/master_records_custody_api.py` was the existing central custody authority but its original governed-transition intake was completed-ALLOW oriented.
- `master-records/orchestration/services/canonical_state_transition_custody.py` now extends the same authority for canonical per-state receipts covering `ALLOW`, `DENY`, `EXECUTED`, `COMPLETED`, `PARTIAL`, `FAILED`, `FAIL_CLOSED`, `OBSERVED`, and `NO_CHANGE`, with exact reconstruction.
- `master-records/orchestration/services/canonical_master_records_api.py` installs that extension on the existing production Master Records app; `render-custody-production.yaml` already starts that canonical app.
- `.github/workers/canonical_state_transition_custody.py` is the reusable resident/client adapter. It prefers the canonical Master Records API and can use the existing exact-byte local Master Records lifecycle ingest/reconstruction path when the same custody authority is mounted locally.
- `.github/workers/reusable_task_master_records_roundtrip.py` remains useful as legacy exact-byte infrastructure, but its MIR-specific packet fanout is not the primary canonical state-recording mechanism.
- `StegOS/stegos/state_transition_custody.py` provides the application-neutral protocol used by governed runtimes.
- `StegOS/stegos/canonical_runtime_lane.py` already emits ingress/egress/lease/closure evidence but historically did not intrinsically send every observed transition to Master Records.
- `StegOS/stegos/mir_profile_runtime.py` now emits canonical custody for current InTr ingress, RTC-007, RTC-008, RTC-009, MIR evidence retention, exact return-packet retention, and fail-closed runtime state.
- Site SV001 custody and SV002 reconstruction modules are task-specific/historical adapters and are migration candidates, not the new ecosystem-wide primary mechanism.
- `RT-INTR-GOVERNED-TRANSITION-001` remains the transition-authority reusable task and `RT-INTR-EVIDENCE-CUSTODY-001` remains the reusable InTr evidence-custody semantic precursor.

## Reusable canonical component

Reusable task: `RT-CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`.

Primary receipt schema: `stegverse.canonical-state-transition-receipt/v1`.

Required result for progression:

```text
state = RECORDED
reconstruction_status = PASS
receipt_sha256 = reconstructed_receipt_sha256
master_records_grants_transition_authority = false
```

A missing transition is never fabricated. A custody failure blocks only progression beyond the observed state; it does not rewrite the state or grant authority.

## MIR correction and adoption

The MIR standing request is now event-driven and explicitly does **not** require a WorkerCoordinator claim/fence to create the event.

Canonical source path:

```text
standing MIR event
-> scripts/execute_mir_event_driven_roundtrip.py
-> build MIR Universal InTr intent
-> build non-authorizing materialization request
   request_grants_execution_authority=false
   claim_or_fence_minted=false
   event_triggered=true
   always_on_receiver_required=false
-> persist materialization request
-> canonical Master Records custody of observed event state
-> Interlock/InTr admission / transition consequence
-> EVENT_EPHEMERAL runtime
-> RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
-> exact MIR destination/return retention
-> canonical Master Records custody after every observed state
-> governed return
```

The standing request now names `scripts/execute_mir_event_driven_roundtrip.py` directly. `scripts/consume_mir_roundtrip_egress_authenticity_request.py` invokes that event driver directly and no longer routes event creation through `refresh_and_execute_resident_task.py` or requires a WorkerCoordinator claim/fence. WorkerCoordinator may still coordinate task ownership elsewhere; it is not MIR event-creation authority.

The prior `workers/mir_roundtrip_transition_probe_worker.py` process adapter is disabled for primary execution and retained only as a bounded conformance comparator. It cannot promote runtime state or custody.

## Current runtime evidence boundary

Canonical source adoption is now present, but there is still no authentic current MIR runtime receipt transported into canonical GitHub truth showing execution of the standing event. No authentic current `current.latest.json`, canonical custody summary, RTC-007/008/009 receipt chain, or governed `STEGVERSE_RETURN_EXIT` has been observed here.

A direct authorized machine execution surface is also not connected to this ChatGPT session, so this session cannot invoke the sovereign event driver on the resident host. That is a tool-access fact only; it is **not** a requirement that an idle runtime or second device exist.

Therefore the current failure boundary is not yet attributable to RTC-007, RTC-008, RTC-009, Master Records, or governed return. The first authentic event execution has not been observed. The next authentic execution must use the existing event-triggered path above; once it starts, canonical Master Records receipts identify the exact first transition that failed to occur or failed to reconstruct.

## Completion boundary

Completion requires authentic runtime evidence showing an event-triggered MIR invocation where every observed transition is canonically retained/reconstructed through Master Records, including RTC-007/008/009 and governed return. Source/tests alone do not satisfy runtime completion.

No second scheduler, dispatcher, WorkerCoordinator, runtime plane, custody authority, user-device prerequisite, or generic SV002 re-proof may be introduced.
