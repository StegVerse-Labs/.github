# ERL Same-Device Portable Execution Mirror Handoff

Updated: 2026-09-13

## Identity

- Parent Goal Task: `SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`
- Component Task ID: `SS-ERL-SAME-DEVICE-PORTABLE-EXECUTION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / SOURCE_IMPLEMENTATION`
- Parent Goal identity preserved: `true`
- New Goal Task minted: `false`

## Purpose

Expose the already-built ERL resident-local manifest -> Universal Interlock/InTr -> DEVICE_KV path through the existing StegOS same-device service-worker execution surface so the canonical parent Goal can obtain authentic task-bound portable execution evidence without requiring Python-only resident execution or another machine.

This component owns only the missing execution-surface adapter. It does not own ERL semantics, Interlock/InTr authority, WorkerCoordinator authority, KV/SKAP authority, credential authority, provider execution, Master Records custody, or parent completion.

## Established rule

Device confirmation is not part of this component.

```text
device discovery required: false
device confirmation required: false
device presence probe required: false
device identity gate: PROHIBITED
remote connected-device enumeration: NOT_APPLICABLE
second user-operated device required: false
physical surface label mints authority: false
```

A continuation MUST NOT discover, confirm, enumerate, poll for, wait for, or require an iPhone, resident device, connected device, Remote Desktop Commander device, or second machine.

## Existing components to reuse

- `StegVerse-Labs/StegOS/mobile/web-bootstrap/service-worker.js`
- existing `stegos-web-bootstrap-v1` IndexedDB state/journal
- existing projected portable WorkerCoordinator implementation from `.github/workercoordinator/portable_checkout.js`
- existing DEVICE_KV owner task `SHWP-DEVICE-KV-INTR-OBSERVATION-001`
- parent ERL full-path contract `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV`
- existing ERL transport semantics from `.github/scripts/submit_erl_active_research_intr_binding_local.py`
- existing terminal DEVICE_KV materialization contract from `.github/scripts/consume_device_kv_intr_materialization_request.py`

No second service worker, listener, scheduler, task registry, WorkerCoordinator, runtime plane, credential path, provider operation, or user-verification path may be introduced.

## Required source behavior

The existing StegOS service worker must expose one bounded same-origin ERL route that:

1. accepts only the exact parent task/COSV and canonical ERL binding/envelope identity;
2. rejects any device-confirmation or device-identity prerequisite;
3. reuses the existing portable WorkerCoordinator state lineage where claim/fence admission is required;
4. applies the existing ERL Universal InTr transition semantics for hop 1 and hop 2;
5. preserves exact operation ID, packet ID, payload hash, prior-receipt lineage, and full-path intent;
6. hands the terminal `DEVICE_SYSTEM -> KV` materialization to the existing DEVICE_KV owner semantics rather than creating a second KV path;
7. emits non-authorizing hash-linked evidence into the existing service-worker journal;
8. never upgrades source installation, route availability, or journal staging into runtime completion.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition/admission authority.
- TV/TVC: credential/provider/release authority where credentials are actually required.
- KV/SKAP Vault: sole user-verification authority.
- StegOS: portable execution substrate only.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: observability/timing/freshness/correlation only.
- GitHub: runtime authority `NONE`.

## Completion boundary

This component is source-complete only when:

- the bounded ERL same-device service-worker route exists;
- exact parent task/COSV and source-binding validation exists;
- device-confirmation/discovery/presence gating is explicitly absent and regression-tested;
- the route reuses the existing portable WorkerCoordinator and journal lineage;
- exact ERL hop/terminal identity continuity is regression-tested;
- StegOS exact-head validation passes;
- the implementation is merged.

Authentic execution, three-hop receipts, terminal KV exact-byte readback, provider-proof binding, and Master Records reconstruction remain parent Goal predicates and are not completed by this child.

## Current state

`MISSING_SAME_DEVICE_ERL_ADAPTER_IDENTIFIED / EXISTING_STEGOS_SERVICE_WORKER_REUSE_REQUIRED / DEVICE_CONFIRMATION_PROHIBITED / SOURCE_IMPLEMENTATION_PENDING / PARENT_RUNTIME_EVIDENCE_UNCHANGED`
