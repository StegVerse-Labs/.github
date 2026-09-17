# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / CANONICAL CUSTODY API MATERIALIZED / MIR SV002 BROWSER EVENT REIMPLEMENTED ON CURRENT UNIVERSAL INTR / AUTHENTIC RUNTIME SEQUENCE PENDING`

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
Required result for progression is `state=RECORDED`, `reconstruction_status=PASS`, exact receipt/reconstruction digest equality, and no Master Records transition authority.

## SV002 initiation invariant

The successful StegVerse-002 sequence was browser-event initiated. Its browser event queued a non-authorizing Universal InTr materialization request into the registered Node outbox, current InTr admitted the exact queued trigger, and only then was the bounded `EVENT_EPHEMERAL` browser Web Worker consequence materialized. No directly reachable machine host, idle runtime, scheduler, dispatcher, WorkerCoordinator event-creation claim/fence, or second user-operated device is required.

Hard reusable constraints remain:

- `EVENT_IS_THE_TRIGGER`;
- `NO_IDLE_RUNTIME_REQUIRED`;
- `NO_REMOTE_HOST_DISCOVERY`;
- `NO_EVENT_CLAIM_OR_FENCE`;
- `CURRENT_INTR_ADMISSION_PRECEDES_RUNTIME`;
- `REUSE_BROWSER_EVENT_RUNTIME_FIXTURE`;
- GitHub/CI runtime authority `NONE`.

## 2026-09-17 MIR correction

The first browser reimplementation still had two defects and therefore could not correctly produce the expected runtime evidence:

1. its hand-built materialization request omitted fields required by the canonical registered-Node `validateMaterializationRequest()` contract, so `queueIntrMaterializationRequest()` could fail closed before the MIR event reached InTr;
2. the browser runtime locally recorded `CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED` without requiring an authentic current `INGRESS_ADMITTED` receipt from `/intr/materialization`.

Those defects are now corrected in source.

The active MIR source path is:

- `StegVerse-Labs/Site:intr-mir-roundtrip-extension.js` — bounded MIR admission extension on the existing root Universal InTr service worker;
- `StegVerse-Labs/Site:stegos-node/mir-roundtrip-intr-sync.js` — exact registered-Node outbox trigger transport to the existing `/intr/materialization` route and strict MIR ingress-receipt validation;
- `StegVerse-Labs/Site:assets/mir-roundtrip-browser-activation.js` — builds a Node-valid Universal InTr request, queues it, requires current InTr admission, records canonical ingress custody, and only then invokes the event runtime;
- `StegVerse-Labs/Site:assets/mir-roundtrip-sv002-browser-runtime.js` — refuses execution without the exact admitted MIR ingress receipt and binds the receipt into the bounded Web Worker execution;
- `StegVerse-Labs/Site:mir-roundtrip/index.html` — autostart browser-event surface loading the MIR sync before activation;
- `StegVerse-Labs/Site:tests/test_mir_sv002_browser_event_reimplementation.py` — source conformance now explicitly checks queue -> InTr admission -> runtime ordering and forbids synthetic ingress promotion.

The existing root service worker remains the sole device-local Universal InTr ingress. `intr-service-worker.js` imports the MIR extension; no second service worker or runtime plane was created.

## Canonical MIR state sequence

The corrected browser path requires Master Records exact custody/reconstruction after each actually observed state:

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

The existing external-counterpart return consumer is reused after exact MIR packet retention. The temporary MIR probe remains comparison-only and cannot substitute for canonical state-transition custody.

## Evidence boundary

The source defect is repaired and the current InTr admission transition is now a hard prerequisite to runtime materialization. No authentic current MIR browser-event execution receipt has yet been observed after this correction, so RTC-007/008/009, `STEGVERSE_RETURN_EXIT`, and full round-trip completion remain unpromoted.

The current GitHub Actions lookup for the newest Site conformance commit returned no associated pull-request workflow runs; therefore no green CI claim is made from that lookup.

## Next action

Observe the corrected `/mir-roundtrip/` browser event. Accept `CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED` only from the exact `stegverse.mir-roundtrip-intr-materialization-ingress/v1` `INGRESS_ADMITTED` receipt, then reconcile Master Records in sequence and repair only the first authentic non-returned transition. Do not reintroduce a Python execution substitute, idle host, remote-host discovery, scheduler, dispatcher, WorkerCoordinator event-creation gate, or second-device dependency.
