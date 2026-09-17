# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / CANONICAL CUSTODY API MATERIALIZED / MIR SV002 BROWSER EVENT REIMPLEMENTED / AUTHORITATIVE MASTER RECORDS WRITE-THROUGH MATERIALIZED / AUTHENTIC RUNTIME SEQUENCE PENDING`

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
Canonical submission schema: `stegverse.master-records.state-transition-submission/v1`.
Authoritative endpoint contract: `/api/master-records/state-transitions`, owned by `master-records/orchestration`.
Required result for progression is `state=RECORDED`, `reconstruction_status=PASS`, exact receipt/reconstruction digest equality, and no Master Records transition authority.

## SV002 initiation invariant

The successful StegVerse-002 sequence remains the immutable execution fixture:

```text
browser event
-> registered StegVerse Node
-> non-authorizing Universal InTr materialization request
-> write-once Node intr_outbox
-> current Interlock/InTr admission
-> bounded EVENT_EPHEMERAL browser Web Worker
-> execution-time runtime identity
-> governed transition consequence
-> canonical state receipt
-> authoritative Master Records custody/reconstruction
```

No directly reachable machine host, idle runtime, scheduler, dispatcher, WorkerCoordinator event-creation claim/fence, Python substitute, or second user-operated device is required.

Hard reusable constraints remain:

- `EVENT_IS_THE_TRIGGER`;
- `NO_IDLE_RUNTIME_REQUIRED`;
- `NO_REMOTE_HOST_DISCOVERY`;
- `NO_EVENT_CLAIM_OR_FENCE`;
- `CURRENT_INTR_ADMISSION_PRECEDES_RUNTIME`;
- `REUSE_BROWSER_EVENT_RUNTIME_FIXTURE`;
- `BROWSER_LOCAL_STORAGE_IS_NOT_AUTHORITATIVE_MASTER_RECORDS_CUSTODY`;
- GitHub/CI runtime authority `NONE`.

## MIR browser implementation

The active MIR source path is:

- `StegVerse-Labs/Site:intr-mir-roundtrip-extension.js` — bounded MIR admission extension on the existing root Universal InTr service worker;
- `StegVerse-Labs/Site:stegos-node/mir-roundtrip-intr-sync.js` — exact registered-Node outbox trigger transport to `/intr/materialization` and strict MIR ingress-receipt validation;
- `StegVerse-Labs/Site:assets/mir-roundtrip-browser-activation.js` — queues the Node-valid materialization request, requires authoritative Master Records custody of the queued transition, requires current InTr admission, requires authoritative Master Records custody of ingress, and only then invokes the event runtime;
- `StegVerse-Labs/Site:assets/mir-roundtrip-sv002-browser-runtime.js` — refuses execution without the exact admitted MIR ingress receipt and submits RTC-007/008/009, destination evidence, and exact return retention through the shared custody object;
- `StegVerse-Labs/Site:assets/canonical-master-records-transition-custody-browser.js` — browser client for the existing canonical Master Records state-transition API; it no longer self-issues `RECORDED` custody from IndexedDB;
- `StegVerse-Labs/Site:data/mir-roundtrip-browser-runtime-binding.v1.json` — binds the authoritative Master Records endpoint and classifies browser storage as `SUBORDINATE_CONTINUITY_ONLY`;
- `StegVerse-Labs/Site:mir-roundtrip/index.html` — deterministic autostart browser-event surface;
- `StegVerse-Labs/Site:tests/test_mir_sv002_browser_event_reimplementation.py` — conformance assertions for SV002 initiation plus authoritative Master Records write-through.

The browser custody client now performs:

```text
build exact canonical state receipt
-> POST exact receipt to authoritative Master Records API
-> require RECORDED
-> require reconstruction_status=PASS
-> require receipt_sha256 == reconstructed_receipt_sha256 == locally calculated canonical digest
-> only after PASS cache the returned authoritative receipt locally
-> progress to next transition
```

Browser IndexedDB is continuity/cache only. The browser may not self-issue custody receipts and may not contain Master Records credential plaintext.

## Source validation

Site source conformance is green for commit `91d12a55a602168a30472ba9ed4489b9066c4b91`, workflow run `35193442678`.

That run validates source semantics only. GitHub Actions runtime authority remains `NONE` and cannot promote any MIR runtime predicate.

## Canonical MIR state sequence

```text
MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED
-> authentic /intr/materialization INGRESS_ADMITTED
-> CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED
-> RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
-> MIR_DESTINATION_EVIDENCE_RETAINED
-> EXACT_GOVERNED_RETURN_PACKET_RETAINED
-> STEGVERSE_RETURN_EXIT or MIR_GOVERNED_RETURN_FAIL_CLOSED
```

Every listed observed state must receive authoritative Master Records `RECORDED + PASS` before the next machine-owned transition progresses.

## Evidence boundary

No authentic current registered-Node MIR outbox entry, current MIR `INGRESS_ADMITTED` receipt, browser EVENT_EPHEMERAL execution receipt, RTC-007/008/009 receipt, or governed-return receipt has been observed in canonical evidence after the authoritative-write-through correction. Those runtime predicates remain false.

The source-level false positive has been removed: browser-local IndexedDB no longer qualifies as authoritative Master Records custody.

The next authentic execution therefore begins at the existing `/mir-roundtrip/` browser event. If authoritative Master Records submission for `MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED` does not return `RECORDED + PASS`, that is the first real custody boundary to repair. If it does return PASS, continue without reinterpretation to authentic `INGRESS_ADMITTED`, RTC-007/008/009, exact return retention, and governed return.

## Prohibited regressions

Do not reintroduce:

- browser-local self-issued Master Records custody;
- a new receipt-egress subsystem;
- a Python runtime substitute;
- idle-host or remote-host discovery;
- a scheduler or dispatcher as event creator;
- WorkerCoordinator claim/fence as event-creation authority;
- a second user-operated device dependency;
- source assertions as runtime evidence.
