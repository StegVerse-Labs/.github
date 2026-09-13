# ERL Same-Device Portable Execution Mirror Handoff

Updated: 2026-09-13

## Identity

- Parent Goal Task: `SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`
- Component Task ID: `SS-ERL-SAME-DEVICE-PORTABLE-EXECUTION-001`
- COSV: `40000100100000`
- Status: `SOURCE_COMPLETE / VALIDATED / MERGED`
- Parent Goal identity preserved: `true`
- New Goal Task minted: `false`
- Parent runtime completion claimed: `false`

## Purpose

This component owned only the missing same-device source exposure for the already-built ERL manifest -> Universal Interlock/InTr -> DEVICE_KV path. It is now source-complete.

It does not own ERL semantics, Interlock/InTr authority, WorkerCoordinator authority, KV/SKAP authority, credential authority, provider execution, Master Records custody, or parent completion.

## Source completion evidence

StegOS issue `#369` was completed by PR `#370`.

```text
validated head: e7e25761be40264c1f79b6184645cdbb3cc73ac9
StegOS CI run: 34781051648
StegOS CI result: SUCCESS
merge commit: 3efbcf7852c2a0082b157683599ce8b4f1938d6d
```

## Established device rule

Device confirmation remains outside this component and outside the parent runtime path.

```text
device discovery required: false
device confirmation required: false
device presence probe required: false
device identity gate: PROHIBITED
remote connected-device enumeration: NOT_APPLICABLE
second user-operated device required: false
physical surface label mints authority: false
```

The merged ERL profile input rejects device/node/execution-surface identity fields rather than requiring them.

## Implemented reuse path

No new route was added. The merged implementation reuses the existing service-worker interface:

```text
POST /stegos-bootstrap/resident-task
-> existing StegOSExternalResidentTask dispatcher
-> ERL_ACTIVE_RESEARCH_INTR_SAME_DEVICE_V1 profile
-> deterministic canonical ERL acquisition envelope/full-path intent
-> canonical generated InTr hop 1: EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM / FORWARDED
-> canonical generated InTr hop 2: STEGOS_ECOSYSTEM -> DEVICE_SYSTEM / FORWARDED
-> terminal DEVICE_SYSTEM -> KV projection retaining original full-path intent + receipt lineage
-> existing SHWP-DEVICE-KV-INTR-OBSERVATION-001 portable WorkerCoordinator claim/fence
-> established DEVICE_KV `stegverse-device-local-intr-v1 / kv_files` write-once persistence
-> exact canonical envelope readback
-> canonical generated InTr hop 3: DEVICE_SYSTEM -> KV / RECEIVED
-> full three-hop chain validation
-> existing hash-linked StegOS journal evidence + replay
```

## Reused canonical components

- existing `mobile/web-bootstrap/service-worker.js` resident-task route;
- existing `StegOSExternalResidentTask` dispatcher;
- existing single `stegos-web-bootstrap-v1` portable WorkerCoordinator state lineage;
- existing `.github` DEVICE_KV owner package `SHWP-DEVICE-KV-INTR-OBSERVATION-001`;
- exact generated browser InTr connector projected byte-for-byte from `generated/connectors/site_browser_intr_connectors.js`;
- established DEVICE_KV browser persistence/readback substrate `stegverse-device-local-intr-v1 / kv_files` already used by canonical Site DEVICE_KV receivers;
- existing service-worker journal for evidence only, never as KV storage.

The earlier source-gap note that no canonical browser-capable DEVICE_KV terminal persistence surface had been found is superseded. Canonical Site documentation and receivers establish the DEVICE_KV IndexedDB substrate and exact readback contract.

## Fixed ERL proof identity

```text
group_id: ERL-RC-CYBER-SABOTAGE-LINEAGE-2026
source_id: ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET
source_url: https://www.cisa.gov/news-events/cybersecurity-advisories/aa25-176a
KV key: 02_Research/ERL/ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET.envelope.json
```

Existing provider proof remains binding-only and is never replayed:

```text
provider file: google-drive:file:1KKBS1drUFVh-czLpmg5koRgDs4YMf-gG
size: 1015
sha256: 94470c58db24e544c3edfcd390cca395375a348879ec3c53451ba517ff917763
provider operation reexecution authorized: false
```

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition authority.
- TV/TVC: credential/provider/release authority where credentials are actually required.
- KV/SKAP Vault: sole user-verification authority.
- StegOS: portable execution substrate only.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: observability/timing/freshness/correlation only.
- GitHub: runtime authority `NONE`.

## Component completion boundary

The component predicates are satisfied at source level:

- existing service worker reused;
- existing resident-task route reused;
- parent task/COSV exact binding implemented;
- device-confirmation/discovery/presence gating absent and regression-tested;
- existing portable WorkerCoordinator lineage reused;
- exact ERL operation/packet/payload/prior-receipt continuity encoded and tested;
- terminal DEVICE_KV owner/storage/readback semantics reused;
- exact-head StegOS CI passed;
- source merged.

Therefore `SS-ERL-SAME-DEVICE-PORTABLE-EXECUTION-001` is terminal as a source component.

## Parent runtime continuation

The parent `SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001` remains active. Source completion does not satisfy its runtime predicates.

Authentic invocation must still establish observed runtime state for:

- actual ERL profile execution on the existing portable surface;
- authentic hop 1 / hop 2 / hop 3 receipts;
- exact operation/packet/payload/prior-receipt continuity;
- terminal KV exact-byte readback;
- complete chain validation;
- provider-proof binding without provider replay;
- Master Records custody acceptance and reconstruction confirmation.

No runtime completion, deployment completion, or Master Records completion is claimed by this component.

## Current state

`SOURCE_COMPONENT_COMPLETE / EXISTING_RESIDENT_TASK_ROUTE_REUSED / DEVICE_CONFIRMATION_PROHIBITED / CANONICAL_DEVICE_KV_BROWSER_SUBSTRATE_REUSED / STEGOS_PR_370_MERGED / PARENT_RUNTIME_EVIDENCE_UNCHANGED`
