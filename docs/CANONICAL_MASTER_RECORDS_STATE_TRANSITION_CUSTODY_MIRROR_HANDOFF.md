# Canonical Master Records state-transition custody mirror handoff

Updated: 2026-09-17
Goal Task ID: `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001`
Parent Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / CANONICAL CUSTODY API MATERIALIZED / REQUIRED EVIDENCE VALIDATION MERGED / AUTHORITATIVE MASTER RECORDS WRITE-THROUGH MATERIALIZED / AUTHENTIC RUNTIME SEQUENCE PENDING`

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
Required result for progression is `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, exact receipt/reconstruction digest equality, exact validation/reconstruction of every required evidence item, and no Master Records transition authority.

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

The canonical sequence still begins with `MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED`. Absence of an authentic retained runtime receipt is not a reason to stop. Trace the existing path to the first deterministic defect, repair only that boundary, and continue forward from the repaired evidence trail.

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


## StegBrowser custody decomposition intake

The 2026-09-17 terminal decomposition of `STEG-BROWSER-RUNTIME-CONNECTION-INGRESS-001` resolved that its immutable invocation uses the Site browser canonical custody client and `/api/master-records/state-transitions`; it does not use the optional Python local adapter.

Two genuinely separable custody-owner tasks now carry the remaining source work:

- `MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001` / `docs/MASTER_RECORDS_STEGBROWSER_ENDPOINT_BINDING_MIRROR_HANDOFF.md` / issue `StegVerse-Labs/.github#2078`: bind the existing browser client to the existing authoritative state-transition custody surface without provider/platform/OS/device lock-in, Render, credential substitution, or a second custody/transport plane, then require authentic `RECORDED + reconstruction_status=PASS` for the exact immutable StegBrowser tuple.
- `CANONICAL-MASTER-RECORDS-LOCAL-ADAPTER-REPAIR-001` / `docs/CANONICAL_MASTER_RECORDS_LOCAL_ADAPTER_REPAIR_MIRROR_HANDOFF.md` / issue `StegVerse-Labs/.github#2079`: repair the separate optional local-adapter contract mismatch without relabeling the state receipt as a lifecycle request, fabricating lifecycle evidence, weakening validation, or claiming it is the immutable browser invocation path.

These tasks remain custody/reconstruction work only. Interlock/InTr transition authority and TV/TVC credential authority are unchanged. Source repair does not prove authentic custody or runtime execution.


## 2026-09-18 Healer consumer adoption correction

Tracing `SHWP-HEALER-SOVEREIGN-SCHEDULER-001` exposed a direct consumer-policy mismatch: its executable handoff declared `continuity.master_records_required=false`. The Healer handoff is corrected to require canonical Master Records custody/reconstruction and to cite the existing canonical custody contract/client. This is consumer adoption of the existing authority separation, not a new custody path, and does not promote any runtime transition. The separately owned `CANONICAL-MASTER-RECORDS-LOCAL-ADAPTER-REPAIR-001` condition remains: the optional local Python adapter must consume the canonical state-transition contract rather than the reusable-task lifecycle ingester, or fail closed on the canonical API path.


## 2026-09-18 local-adapter child reconciliation

`CANONICAL-MASTER-RECORDS-LOCAL-ADAPTER-REPAIR-001` is now retired as a validated, merged source repair. PR `#2136` merged at `a21bbeb53e33210d4ac832f343582c02149d8c53`. The merged worker/test blobs exactly match the previously validated artifacts from run `35393803641` / job `105757920409`.

The repaired local path no longer routes canonical state-transition receipts through the reusable-task lifecycle ingester. It reuses the existing `master-records/orchestration` canonical state-transition custody implementation and fails closed without explicit durable Master Records configuration.

This satisfies the parent source predicate for the optional local adapter only. The parent remains `ACTIVE` because authentic runtime custody/reconstruction for governed transitions is still not observed. No runtime execution, custody write, Interlock/InTr transition, TV/TVC credential action, scheduler, dispatcher, exporter, second custody authority, or device dependency is inferred from the source merge.


## 2026-09-18 local adapter child reconciliation

`CANONICAL-MASTER-RECORDS-LOCAL-ADAPTER-REPAIR-001` is source-repair complete and retired. Replacement PR `#2136` merged as `a21bbeb53e33210d4ac832f343582c02149d8c53`. The optional local client now routes canonical state-transition receipts through the existing authoritative `master-records/orchestration` state-transition custody implementation and no longer feeds them into the reusable-task lifecycle ingester.

This closes only the local-adapter source defect. The parent remains ACTIVE because authentic runtime custody/reconstruction evidence is still pending. No authentic Healer, MIR, StegBrowser, RTC-007/008/009, or governed-return Master Records write is inferred from source merge or CI.


## Required evidence closure — 2026-09-18

The canonical rule is now explicit: **all required evidence that results from a governed state transition must be validated by Master Records before that transition may be treated as evidence-complete for further machine-owned progression.**

The transition receipt now carries `required_evidence_manifest`. An empty manifest is valid only when the transition produces no additional required evidence beyond the canonical state receipt itself. Every non-empty item must include exact content, encoding, SHA-256, evidence identity/type, and the same `origin_transition_id`.

The existing `master-records/orchestration` canonical state-transition custody service was extended in PR `#101` and merged as `32d89da201c4653413c85510bec629124b2e3a25`. Its source-validation suite was green before merge. The service now:

- validates that the complete required-evidence manifest is structurally present;
- binds every item to the same transition;
- recomputes and verifies each item digest before accepting custody;
- retains each item alongside the transition receipt;
- reconstructs each required item independently;
- returns per-item validation status and overall `required_evidence_validation_status`;
- fails closed if any required item is missing, malformed, misbound, digest-mismatched, or unreconstructable.

Any validation required by a governed transition executes on that existing transition path before evidence closure. Its output is required transition evidence and must enter the manifest. The existence of another validation function is never a reason to wait, defer, or stop tracing the evidence path.

The existing separation of powers remains unchanged: Interlock/InTr authorizes transitions; TV/TVC holds credential authority where required; Master Records validates/retains/reconstructs observed evidence and grants no transition, execution, governance, credential, publication, deployment, or release authority.

Source merge establishes the required-evidence validation mechanism only. Authentic runtime completion still requires a real governed transition whose receipt and complete required-evidence manifest return `RECORDED + reconstruction_status=PASS + required_evidence_validation_status=PASS`.


## Canonical registry projection reconciliation — 2026-09-18

During this required-evidence refinement, the canonical task shard and handoff were confirmed current and active, but `CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001` was not present in the monolithic `data/canonical-task-registry.json`. The existing task was therefore projected into the monolithic registry; no new Goal identity was created.

The proposed registry generation advances exactly one generation from the then-current value and carries the existing task's COSV `50000000100000`, parent/root relationships, authority boundaries, and required-evidence validation contract unchanged.

This is coordination repair only. It does not create a second custody service, transition engine, scheduler, dispatcher, WorkerCoordinator plane, credential authority, runtime, or device dependency.


## First required-evidence carriage defect and repair — 2026-09-18

Master Records repository evidence was searched for an authentic post-contract transition result containing all three required progression fields:

```text
state=RECORDED
reconstruction_status=PASS
required_evidence_validation_status=PASS
```

No authentic runtime receipt carrying that complete result was present in the repository evidence. That did not become a waiting condition. The existing transition source was traced from the first canonical MIR transition forward.

The first deterministic defect was found at `MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED`: the materialization request was persisted and referenced by the transition evidence, but the exact materialization object was not included as a `required_evidence_manifest` item. Because the materialization request is a direct result of that transition, the new Master Records invariant requires it to be validated and reconstructed.

The existing driver now binds the exact materialization object as canonical-json required evidence with:

- evidence type `MIR_MATERIALIZATION_REQUEST`;
- origin transition `MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED`;
- exact canonical SHA-256;
- exact structured content.

The downstream StegOS transition-custody protocol was also repaired on the existing path. PR `StegVerse-Labs/StegOS#395` merged as `3e60f6f5ef0f8516c66ba51a1bb2c78f8b13f3e7`. Every observed MIR transition carried through `retain_observed_transition` now supplies its exact transition-evidence object to Master Records as required evidence and refuses progression unless Master Records returns all three progression predicates above.

No second validator, custody store, runtime, scheduler, dispatcher, transition authority, credential path, or device dependency was created.
