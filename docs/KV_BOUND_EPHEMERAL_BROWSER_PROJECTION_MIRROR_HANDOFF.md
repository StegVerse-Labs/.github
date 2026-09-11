# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-11

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / TASK-0011 G7 FENCE7 AUTHENTIC / FROZEN SITE PRODUCT MERGED AND PUBLIC / SAME-DEVICE KV RECOVERY MERGED AND PUBLIC / CURRENT-IPHONE RUNTIME PENDING`

## Canonical architecture

KV is the private governed continuity boundary. Browser presentation is ephemeral. Interlock/InTr owns transition/admission; WorkerCoordinator/canonical allocator owns claim/fence; TV/TVC owns credentials/provider operations; HB is observability only; GitHub Actions are validation/evidence transport only. No Render or hosted fallback is admissible.

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

The wrapper removes the saved-projection-file dependency from the normal path. It reuses the existing current-device stack:

```text
Device -> KV InTr request
-> authentic ingress receipt
-> KV_INSTALLATION_VERIFIED required
-> current browser capability observation
-> exact CURRENT_IPHONE_TESTFLIGHT_SIGNING projection derived in memory
-> frozen executeStaticCurrentIphoneTestflightBootstrap({projectionContext})
-> TV/TVC-owned signing/provider path
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

Source, CI, merge, and publication are not TestFlight/runtime proof.

## Current first unresolved predicate

`TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED`

Next authentic execution surface:

```text
https://stegverse.org/task0011-same-device-kv-recovery.html
```

On the established current iPhone, tap `Use This iPhone's KV and Prepare IPA`. Preserve the complete displayed result or exact fail-closed message. No projection JSON selection is required on the normal path.

If the exact failure is `resident KV installation not verified`, use `Admit Existing KV Installation Receipt` only if the canonical `_System/installation.receipt.json` is available, then allow the page to retry. If a different fail-closed message appears, preserve it exactly and do not clear Safari/site/KV/node state.

TV/TVC remains Apple credential/provider authority. Signing success must precede any Build Upload/TestFlight/runtime completion claim.

## README state

Site `README.md` was reviewed against this bounded recovery slice. Its public-mirror and authority-boundary semantics remain correct; the new wrapper is an operational same-device rendezvous, not a new Site authority plane. No repository-wide semantic rewrite was required.

## Manual work

On the established current iPhone, open `https://stegverse.org/task0011-same-device-kv-recovery.html`, tap `Use This iPhone's KV and Prepare IPA`, and preserve the exact displayed result or exact fail-closed message. Do not clear Safari/site/KV/node continuity state and do not switch devices. If the page specifically reports `resident KV installation not verified`, tap `Admit Existing KV Installation Receipt` only if you have the canonical `_System/installation.receipt.json` available.
