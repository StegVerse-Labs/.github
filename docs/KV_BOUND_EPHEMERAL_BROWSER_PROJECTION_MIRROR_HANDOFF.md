# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-12

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / GOAL IDENTITY PRESERVED / REUSABLE COMPONENT RECONCILIATION SOURCE PENDING VALIDATION / TASK-0011 G7 FENCE7 AUTHENTIC / FROZEN SITE PRODUCT MERGED AND PUBLIC / SAME-DEVICE KV RECOVERY MERGED AND PUBLIC / CURRENT-IPHONE RUNTIME PENDING`

## Reusable Task Component Model reconciliation

Canonical model source is `.github` PR #1652 at merge commit `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

Deterministic decomposition score: `30`.
Disposition: `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

The Goal Task remains `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`; COSV remains `50000010100000`. Componentization does not restart, rename, duplicate, close, or complete the Goal Task.

Canonical component projection is recorded separately in:

- `data/goal-task-component-profiles/KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001.json`
- `data/goal-task-transport-profiles/KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001.json`
- `docs/KV_BOUND_EPHEMERAL_BROWSER_PROJECTION_COMPONENT_MODEL_MIRROR_HANDOFF.md`

Selected reusable composition uses the existing execution-materialization contract, existing Device->KV governed ingress, `RTC-MANIFEST-001`, repeatable `RTC-INTERLOCK-INTR-TRANSPORT-008`, repeatable `RTC-ROUNDTRIP-003`, existing TV/TVC-owned session/provider/release path, the existing current-iPhone TVC translator, existing validators/runtime observers, `RTC-FARSIDE-FINAL-009`, and `RTC-EVIDENCE-CUSTODY-004` under Master Records.

No genuinely new reusable component is required. The Site same-device wrapper, frozen bootstrap, current-iPhone TVC adapter, historical file-selection page, and retired binary relay remain provenance/task-configuration surfaces and must not grow into generic orchestration owners.

This handoff remains runtime truth. Source componentization does not satisfy `TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED` or any downstream runtime/custody predicate.

## Canonical architecture

KV is the private governed continuity boundary. Browser presentation is ephemeral. Interlock/InTr owns transition/admission; WorkerCoordinator/canonical allocator owns claim/fence; TV/TVC owns credentials/provider operations; HB is observability only; GitHub Actions are validation/evidence transport only. No Render or hosted fallback is admissible.

KV/SKAP Vault remains sole user-verification authority. StegOS devices are interchangeable transport/execution nodes and have no user-verification authority. Master Records owns observed-reality custody and reconstruction.

## Authentic retained evidence

TASK-2026-0011 is authentically allocated on the established current iPhone at generation 7 / fence 7 with `ALLOCATION_COMPLETE`, `CLAIM_GRANT_OBSERVED`, journal replay PASS, and no allocator retry required.

Two prior authentic `CURRENT_IPHONE_TESTFLIGHT_SIGNING` projections were accepted with:

```text
primary sha256 93caa302f310be097005c21639504bc13a7e8090d161d56cd0823c37363db3f8
repeat  sha256 064c8fcac9e1ee87c6f6dc73807689fded772865ae4b3f461b304d26aaf7df64
entry_state ADMITTED
browser_capability_state OBSERVED_COMPATIBLE
persistence_effect NONE_EPHEMERAL_CONTEXT_ONLY
authority_effect NONE_PROJECTION_GATE_ONLY
```

The operator later reported that no valid saved projection file remained conveniently available and candidate files on hand all failed closed at the frozen bootstrap. This is treated as a recoverable usability condition, not authority to synthesize a projection.

## Frozen TASK-0011 product remains exact

Site PR `#1236` merged at `841ab0298741fd5152c9cf88211468c3b86093d3`. Post-merge validation run `34615914477` passed. Public exact proof run `34616154322` matched the live frozen HTML/bootstrap/KV-loader/signer Git blobs and exact IPA/WASM SHA-256 + sizes.

No frozen `stegos-bootstrap/` product bytes were changed by the recovery work.

## Same-device recovery repair

Site PR `#1237` added a separate wrapper and squash-merged at:

```text
b847d4e408571efb9ff511f1facbc3f38128846d
```

Public route:

```text
https://stegverse.org/task0011-same-device-kv-recovery.html
```

The wrapper removes the saved-projection-file dependency from the normal path. Under the component model it is a task-specific composition/rendezvous surface that reuses existing governed capabilities rather than owning them.

Normal path:

```text
Device -> KV InTr request
-> authentic ingress receipt
-> KV_INSTALLATION_VERIFIED required
-> current browser capability observation
-> exact CURRENT_IPHONE_TESTFLIGHT_SIGNING projection derived in memory
-> frozen executeStaticCurrentIphoneTestflightBootstrap({projectionContext})
-> existing TV/TVC-owned provider/release path
```

The wrapper does not mint admission, synthesize commitments, bypass `KV_INSTALLATION_VERIFIED`, persist projection state in browser storage, or alter credential/claim authority.

If and only if the resident KV installation itself is not verified, the page exposes the pre-existing `Admit Existing KV Installation Receipt` recovery control. That fallback still requires the canonical `_System/installation.receipt.json`; it does not invent or reconstruct the receipt.

## Validation evidence

Exact PR head `2a3df27277ce2d10c0e6a5f1ae7dabd06adbb0d1` passed:

```text
Site Bootstrap Validate       run 34635756191 SUCCESS
Ecosystem Heartbeat           run 34635756202 SUCCESS
Site Handoff Orchestrator     run 34635756331 SUCCESS
```

Credential-free public publication proof run `34635855832` completed successfully and observed the live wrapper with the required same-device projection materializer, direct frozen-bootstrap invocation, and no browser-persistence markers.

Source, CI, merge, publication, and component reuse are not TestFlight/runtime proof.

## Current first unresolved predicate

`TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED`

Next authentic execution surface:

```text
https://stegverse.org/task0011-same-device-kv-recovery.html
```

After this component-model reconciliation validates and merges, continue through the existing same-device execution surface. Preserve the complete displayed result or exact fail-closed message. Classify any authentic failure by the owning component; repair that component only, without adding parallel task-specific orchestration.

TV/TVC remains Apple credential/provider/release authority. Signing success must precede any Build Upload/TestFlight/runtime completion claim. Master Records custody/reconstruction remains required before final Goal Task completion and return to the frozen global measurement.

## README state

The `.github` root README already contains the canonical Reusable Task Component Model projection from PR #1652. This reconciliation does not materially change repository-wide function. Site `README.md` remains accurate for its public-mirror and authority semantics. No additional README mutation is required for this reconciliation.

## Manual work

None while the component-model reconciliation is in source validation. After merge, the next authentic action remains the established current-iPhone same-device execution described above.
