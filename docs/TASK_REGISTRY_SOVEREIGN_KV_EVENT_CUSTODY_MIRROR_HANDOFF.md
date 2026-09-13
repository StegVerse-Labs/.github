# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
COSV: not established
Status: `ACTIVE / CHECKED_OUT / COMPONENT COMPOSITION MERGED / CURRENT EVIDENCE SELECTOR MERGED / RUNTIME WRITE + READBACK PENDING`

## Current state

PR #1671 merged the reusable-component composition at `64c388bdd374adcc81bec50ec21d4987624e5362`.
PR #1714 merged `RTC-EVIDENCE-CURRENT-SELECTOR-010` at `00d4f3ab4ebd397090c2953de6f2c6155eafe6d5`; exact head `c6a21dea8d93ba129647058c022711cccd16344e` passed organization-control `34738000652`, deterministic-suite `34738000664`, and Heartbeat `34738000657`.

Selected components remain `RTC-MANIFEST-001`, `RTC-GOVERNED-PROCESSING-002`, repeatable `RTC-ROUNDTRIP-003`, `RTC-EVIDENCE-CUSTODY-004`, `RTC-STEGVERSE-EGRESS-007`, repeatable `RTC-INTERLOCK-INTR-TRANSPORT-008`, `RTC-FARSIDE-FINAL-009`, and `RTC-EVIDENCE-CURRENT-SELECTOR-010`.

## Runtime owner reconciliation

`STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` remains the canonical Device/KV/SKAP runtime Goal and is `ACTIVE / CHECKED_OUT` on `main` with its unresolved authentic runtime predicates intact.

The proposed `STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002` successor was created only because the parent reached a prompt-count ceiling. The canonical decomposition policy prohibits splitting merely to reset prompt count. PR #1519 is therefore closed unmerged as superseded, and issue #1500 is closed as superseded/not planned. Its historical validation remains provenance only. No runtime predicate or authority moved.

This Goal continues to depend directly on `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`.

## Runtime boundary

No authentic `stegverse.task-registry-sovereign-kv-projection-receipt/v1`, provider WRITE, or exact event-hash readback has been established. Fresh GitHub evidence remains source/contracts/tests/handoffs, and the connected Drive searches returned no matching custody artifact.

First unresolved predicate:
`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

Terminal completion still requires live exact-hash event binding, applicable claim/fence and transition evidence, current KV/SKAP evidence selection when required, authentic provider WRITE, exact stored-event hash readback, accepted projection receipt, and required Master Records reconstruction.

## Authority

Task Registry is coordination only. WorkerCoordinator owns claim/fence. Interlock/InTr owns transition/admission. TV/TVC owns provider release. KV/SKAP Vault is sole user-verification authority. StegOS devices are interchangeable transport/execution nodes. Master Records owns custody/reconstruction. HeartBeat is observability only. GitHub runtime authority is `NONE`.

## Next

Observe `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` and the existing provider lineage for an authentic admitted WRITE. Once it exists, perform the exact-hash readback round trip through the existing validator and require Master Records reconstruction. Do not create duplicate runtime, transport, selector, credential, custody, or prompt-reset successor paths.

## README

Reviewed; no repository-level change required.

## Manual work

None.
