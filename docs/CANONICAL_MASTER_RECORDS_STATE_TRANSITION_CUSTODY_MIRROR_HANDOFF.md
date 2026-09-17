# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / INVENTORY COMPLETE / CANONICAL CUSTODY API MATERIALIZED / MIR SOURCE ADOPTED / SV002 BROWSER-EVENT INITIATION CORRECTED / AUTHENTIC RUNTIME SEQUENCE PENDING`

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
- `master-records/orchestration/services/canonical_state_transition_custody.py` extends the same authority for canonical per-state receipts covering `ALLOW`, `DENY`, `EXECUTED`, `COMPLETED`, `PARTIAL`, `FAILED`, `FAIL_CLOSED`, `OBSERVED`, and `NO_CHANGE`, with exact reconstruction.
- `master-records/orchestration/services/canonical_master_records_api.py` installs that extension on the existing production Master Records app; `render-custody-production.yaml` starts that canonical app.
- `.github/workers/canonical_state_transition_custody.py` is the reusable resident/client adapter. It prefers the canonical Master Records API and can use the existing exact-byte local Master Records lifecycle ingest/reconstruction path when the same custody authority is mounted locally.
- `.github/workers/reusable_task_master_records_roundtrip.py` remains useful as legacy exact-byte infrastructure, but its MIR-specific packet fanout is not the primary canonical state-recording mechanism.
- `StegOS/stegos/state_transition_custody.py` provides the application-neutral protocol used by governed runtimes.
- `StegOS/stegos/mir_profile_runtime.py` emits canonical custody for current InTr ingress, RTC-007, RTC-008, RTC-009, MIR evidence retention, exact return-packet retention, and fail-closed runtime state.
- Site SV001 custody and SV002 reconstruction modules are task-specific/historical adapters and are migration candidates, not the ecosystem-wide primary mechanism.

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

## Detailed SV002 initiation correction

A deeper review of the successful StegVerse-002 experiment corrects the prior execution-host assumption.

The successful SV002 sequence did **not** require ChatGPT, Remote Desktop, a resident shell, or another machine connector to find and invoke a pre-existing runtime. Its execution surface was the Site browser event itself:

```text
sv002-observe/index.html
-> assets/sv002-observe.js observation event
-> canonical Interlock/InTr attempt
-> if receiver unavailable, build exact non-authorizing Universal InTr materialization request
-> queue request into the registered StegVerse Node intr_outbox
-> assets/sv002-local-runtime-materializer.js materialize(queued)
-> Blob-backed EVENT_EPHEMERAL browser Web Worker
-> principal execution
-> execution receipt
-> independent Master Records reconstruction
```

`stegos-node/sv002-intr-sync.js` separately attempted pending outbox synchronization on `DOMContentLoaded` and `online`, but that network synchronization was non-authorizing and its ingress receipt explicitly reported `runtime_execution_attempted=false`. The local browser materializer was the execution mechanism.

The validated reuse documentation is explicit: the SV002 execution mechanics are the fixture and must not be reconstructed as a new Python/runtime path. Current invocation work may change only Goal/COSV/manifest/destination bindings while preserving Node gating, Interlock/InTr materialization, bounded lease, EVENT_EPHEMERAL browser Web Worker construction, execution-time runtime identity, and reconstruction behavior.

The Site already contains a newer derived execution surface at `stegos-bootstrap/canonical-work-runtime-consumption.html`; it supports `?autostart=1`, drives the existing root Universal InTr service worker, and continues admitted work into the already-existing SV002-derived browser materializer. This confirms that a browser event activation surface, not an idle machine host, is the canonical initiation pattern.

Canonical preflight: `receipts/preflight/MIR-SV002-INITIATION-MECHANISM-001.json`.

## MIR consequence

The present Python `scripts/execute_mir_event_driven_roundtrip.py` may remain useful as source/conformance scaffolding, but it must not be treated as the final duplicated SV002 execution surface. MIR must receive a Site/browser event activation binding that reuses the validated SV002 browser mechanics and changes only MIR-specific Goal/COSV/destination/custody bindings.

Therefore the current blocker is **not** `NO_AUTHORIZED_MACHINE_EXECUTION_HOST`. Lack of a Remote Desktop or direct-machine connector is irrelevant to the proven experiment mechanism.

The next source transition is to materialize the MIR browser-event initiation surface from the validated Site fixture, preserve canonical Master Records custody after each observed transition, and then invoke/observe that event path. No new Python runtime, scheduler, dispatcher, WorkerCoordinator event-creation gate, external host discovery path, or second device may be introduced.

## Completion boundary

Completion requires authentic runtime evidence showing an event-triggered MIR invocation where every observed transition is canonically retained/reconstructed through Master Records, including RTC-007/008/009 and governed return. Source/tests alone do not satisfy runtime completion.
