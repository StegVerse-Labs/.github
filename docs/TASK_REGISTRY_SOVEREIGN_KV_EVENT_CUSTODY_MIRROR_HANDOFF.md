# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
COSV: not established
Status: `ACTIVE / CHECKED_OUT / COMPONENT COMPOSITION MERGED / CURRENT EVIDENCE SELECTOR MERGED / RUNTIME WRITE + READBACK PENDING`

## Current state

PR #1671 merged the canonical reusable-component composition at `64c388bdd374adcc81bec50ec21d4987624e5362`.

PR #1714 merged the current applicable verification selector binding at `00d4f3ab4ebd397090c2953de6f2c6155eafe6d5`. Its exact head `c6a21dea8d93ba129647058c022711cccd16344e` passed organization-control `34738000652`, deterministic-suite `34738000664`, and Heartbeat `34738000657`.

Selected reusable capabilities are `RTC-MANIFEST-001`, `RTC-GOVERNED-PROCESSING-002`, repeatable `RTC-ROUNDTRIP-003`, `RTC-EVIDENCE-CUSTODY-004`, `RTC-STEGVERSE-EGRESS-007`, repeatable `RTC-INTERLOCK-INTR-TRANSPORT-008`, `RTC-FARSIDE-FINAL-009`, and `RTC-EVIDENCE-CURRENT-SELECTOR-010`.

`RTC-EVIDENCE-CURRENT-SELECTOR-010` is non-authorizing. It may select exactly one current applicable already-verified KV/SKAP record. It creates no verification, does not use device identity as verification, and exposes no secret material.

Existing provider and Device/KV/SKAP runtime owners remain unchanged until a successor is canonical on `main`. Candidate successor `STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002` is tracked by issue #1500 and stale/unmerged PR #1519. PR #1519 exact head `a3c66f7a0a17ca941be72cc63f2cb9d11134b686` passed runs `34637852384`, `34637852390`, and `34637852446`, but it is not canonical source truth.

## Runtime boundary

Fresh GitHub search finds `stegverse.task-registry-sovereign-kv-projection-receipt/v1` only in source, contracts, tests, and handoffs. Fresh connected Drive searches for this Goal Task ID and the projection receipt returned no matches. No authentic runtime projection receipt, provider WRITE, or exact event-hash readback is established.

First unresolved predicate:
`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

Terminal completion still requires live exact-hash event binding, applicable claim/fence and transition evidence, current KV/SKAP evidence selection when required, authentic provider WRITE, exact stored-event hash readback, accepted projection receipt, and required Master Records reconstruction.

## Authority

Task Registry remains coordination only. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains provider-release authority. KV/SKAP Vault remains sole user-verification authority. StegOS devices remain interchangeable transport/execution nodes. Master Records remains custody/reconstruction authority. HeartBeat remains observability only. GitHub runtime authority remains `NONE`.

## Next

Continue observing the existing canonical runtime owners for an authentic admitted provider WRITE. Rebind to `STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002` only after its owner transfer becomes canonical on `main`. Once WRITE evidence exists, execute the second governed round trip for exact-hash readback through the existing validator, then require Master Records reconstruction before terminal completion. Do not create duplicate runtime, transport, selector, credential, or custody paths.

## README

Reviewed; no repository-level update is required.

## Manual work

None.
