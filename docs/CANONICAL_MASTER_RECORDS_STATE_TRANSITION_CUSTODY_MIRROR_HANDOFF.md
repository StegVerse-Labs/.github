# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / INVENTORY COMPLETE / CANONICAL CUSTODY API MATERIALIZED / MIR SV002 BROWSER-EVENT SOURCE REIMPLEMENTED / AUTHENTIC RUNTIME SEQUENCE PENDING`

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

## SV002 initiation invariant

The successful StegVerse-002 sequence was browser-event initiated. Its browser event queued a non-authorizing Universal InTr materialization request into the registered Node outbox, then the existing local materializer created a Blob-backed `EVENT_EPHEMERAL` browser Web Worker. No directly reachable machine host or idle runtime was required.

Hard reusable constraints are now:

- `EVENT_IS_THE_TRIGGER`;
- `NO_IDLE_RUNTIME_REQUIRED`;
- `NO_REMOTE_HOST_DISCOVERY`;
- `NO_EVENT_CLAIM_OR_FENCE`;
- `MATERIALIZATION_PRECEDES_RUNTIME`;
- `REUSE_BROWSER_EVENT_RUNTIME_FIXTURE`;
- GitHub/CI runtime authority `NONE`.

Canonical preflight: `receipts/preflight/MIR-SV002-INITIATION-MECHANISM-001.json`.

## MIR reimplementation

The previous Python event driver is no longer treated as the final execution substrate. The actual MIR Site/browser source now consists of:

- `StegVerse-Labs/Site:data/mir-roundtrip-browser-runtime-binding.v1.json`;
- `StegVerse-Labs/Site:assets/canonical-master-records-transition-custody-browser.js`;
- `StegVerse-Labs/Site:assets/mir-roundtrip-sv002-browser-runtime.js`;
- `StegVerse-Labs/Site:assets/mir-roundtrip-browser-activation.js`;
- `StegVerse-Labs/Site:mir-roundtrip/index.html`;
- `StegVerse-Labs/Site:tests/test_mir_sv002_browser_event_reimplementation.py`;
- `StegVerse-Labs/Site:.github/workflows/mir-sv002-browser-event-conformance.yml`.

The browser page autostarts the unchanged MIR event. The activation surface requires an already-registered StegVerse Node, queues a non-authorizing write-once materialization request, and invokes the bounded `EVENT_EPHEMERAL` browser Web Worker. It performs no remote-host discovery and does not require WorkerCoordinator claim/fence to create the event.

## Canonical MIR state sequence

The browser path requires Master Records exact custody/reconstruction after each actually observed state:

```text
MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED
CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED
RTC-STEGVERSE-EGRESS-007
RTC-INTERLOCK-INTR-TRANSPORT-008
RTC-FARSIDE-FINAL-009
MIR_DESTINATION_EVIDENCE_RETAINED
EXACT_GOVERNED_RETURN_PACKET_RETAINED
STEGVERSE_RETURN_EXIT or MIR_GOVERNED_RETURN_FAIL_CLOSED
```

The existing external-counterpart return consumer is reused after exact MIR packet retention. The temporary MIR probe remains comparison-only and cannot substitute for this canonical path.

## Evidence boundary

Source reimplementation is materialized. No authentic current MIR browser-event execution has yet been observed, so RTC-007/008/009, `STEGVERSE_RETURN_EXIT`, and full round-trip completion remain unpromoted. Source tests/workflow are validation only and cannot promote runtime evidence.

The correct next runtime evidence source is the browser event at `/mir-roundtrip/`, not a machine connector, idle resident host, replacement Python runtime, scheduler, dispatcher, or second device.
