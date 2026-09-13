# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
COSV: not established
Status: `ACTIVE / CHECKED_OUT / COMPONENT COMPOSITION MERGED / CURRENT EVIDENCE SELECTOR BOUND / RUNTIME WRITE + READBACK PENDING`

## Current state

PR #1671 merged the canonical reusable-component composition at `64c388bdd374adcc81bec50ec21d4987624e5362`. The goal keeps its existing identity and unresolved runtime predicate.

Selected reusable capabilities are `RTC-MANIFEST-001`, `RTC-GOVERNED-PROCESSING-002`, repeatable `RTC-ROUNDTRIP-003`, `RTC-EVIDENCE-CUSTODY-004`, `RTC-STEGVERSE-EGRESS-007`, repeatable `RTC-INTERLOCK-INTR-TRANSPORT-008`, `RTC-FARSIDE-FINAL-009`, and `RTC-EVIDENCE-CURRENT-SELECTOR-010`.

`RTC-EVIDENCE-CURRENT-SELECTOR-010` is non-authorizing. It may select exactly one current applicable already-verified KV/SKAP record for the operation. It does not create verification, does not use device identity as verification, and does not expose secret material.

Existing provider and Device/KV/SKAP runtime owners remain unchanged until a successor is canonical on `main`. Candidate successor `STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002` is tracked by issue #1500 and PR #1519. PR #1519 exact head `a3c66f7a0a17ca941be72cc63f2cb9d11134b686` passed runs `34637852384`, `34637852390`, and `34637852446`, but is still unmerged, so this goal does not promote it into canonical dependency truth.

## Runtime boundary

Fresh source search still finds `stegverse.task-registry-sovereign-kv-projection-receipt/v1` only in source, contracts, tests, and handoffs. No authentic runtime projection receipt, provider WRITE, or exact event-hash readback has been established.

First unresolved predicate:
`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

Terminal completion still requires the live exact-hash event binding, applicable runtime admission evidence, current KV/SKAP evidence selection when required, provider WRITE, exact stored-event hash readback, accepted projection receipt, and required Master Records reconstruction.

## Authority

Task Registry remains coordination only. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains provider-release authority. KV/SKAP Vault remains sole user-verification authority. StegOS devices remain interchangeable transport/execution nodes. Master Records remains custody/reconstruction authority. HeartBeat remains observability only. GitHub runtime authority remains `NONE`.

## Next

Merge this selector binding only after exact-head validation is green. Continue observing existing runtime owners. Rebind to the successor only if it becomes canonical. Do not create duplicate runtime, transport, selector, or custody paths.

## README

Reviewed; no repository-level update is required.

## Manual work

None.
