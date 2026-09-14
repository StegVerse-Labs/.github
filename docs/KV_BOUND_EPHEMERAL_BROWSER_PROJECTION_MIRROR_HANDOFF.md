# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-13

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / GOAL IDENTITY PRESERVED / TASK-0011 G7 FENCE7 AUTHENTIC / SAME-DEVICE KV RECOVERY PUBLIC / NATIVE TVC BUILD-UPLOAD SOURCE COMPOSED, MERGED, AND PUBLIC / CURRENT-IPHONE RUNTIME PENDING`

## Reusable Task Component Model reconciliation

Canonical model: `.github` PR #1652 at `b9f8e5153aa1651f2d7f043fb902eacb7c113ed9`.

Goal-specific reconciliation: `.github` PR #1679 at merge commit `f76bc12fcb516e68f3acf9ec5b6252e526478bbe`, exact head `d66c8832de479b33473cdfd447d1bf0efa9b1689`.

Exact-head validation passed before merge:

- organization control run `34731043513`: PASS;
- deterministic repository suite run `34731043374`: PASS;
- Heartbeat/repository validation run `34731043427`: PASS.

Deterministic decomposition score: `30`.
Disposition: `STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION`.

The Goal Task remains `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`; COSV remains `50000010100000`. Componentization changes source composition only and does not complete any runtime predicate.

## Authority model

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes; user-verification authority `NONE`.
- Master Records: observed-reality custody and reconstruction authority.
- HeartBeat: synchronization, timing, freshness, liveness, state correlation, and observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

## Retained authentic allocator and public recovery truth

TASK-2026-0011 remains authentically allocated on the established current iPhone at generation 7 / fence 7 with `ALLOCATION_COMPLETE`, `CLAIM_GRANT_OBSERVED`, and journal replay PASS.

Frozen Site product: PR #1236 merged at `841ab0298741fd5152c9cf88211468c3b86093d3`; public exact proof run `34616154322` passed.

Same-device recovery: Site PR #1237 merged at `b847d4e408571efb9ff511f1facbc3f38128846d`; public publication proof run `34635855832` passed.

Public runtime entrypoint:

```text
https://stegverse.org/task0011-same-device-kv-recovery.html
```

The normal path reuses current-device Device->KV admission, requires `KV_INSTALLATION_VERIFIED`, derives the exact `CURRENT_IPHONE_TESTFLIGHT_SIGNING` projection in memory, and continues through the existing TV/TVC-owned provider/release path. If and only if resident KV installation is not verified, the existing installation-receipt recovery remains conditional and requires the canonical `_System/installation.receipt.json`; no receipt may be synthesized.

## Native App Store Connect and TestFlight source composition

The previously identified source seams are now composed through existing owners rather than new authority planes.

### TVC provider/session composition

```text
StegVerse-Labs/TVC PR #424
merge commit: 80db8f1e90168a54e4d44f6b7c3b0ce014c2ebba
```

The secret-free current-iPhone App Store Connect request now maps through the existing short-lived TVC capability lease, canonical broker boundary, current Apple SKAP custody resolver, and callback-only provider executor. The repair also reconciled the persisted Apple sealed-material reference representation while preserving root containment and exact `#sealed_material` binding.

### TVC native TestFlight byte ingress

```text
StegVerse-Labs/TVC PR #428
merge commit: 46878481c23efd9b7d2cd17fc9f701616e687b22
```

The current-iPhone TVC surface now accepts the existing secret-free `UPLOAD_TESTFLIGHT_BUILD` descriptor plus the already-verified signed IPA bytes in the same execution. TVC revalidates exact artifact ref/hash/size/bundle/app bindings, resolves current purpose-bound Apple SKAP custody, and invokes the existing native App Store Connect Build Upload transaction. The byte-ingress path does not persist signed IPA bytes and does not move credential/provider/release authority away from TV/TVC.

### StegOS same-execution caller

```text
StegVerse-Labs/StegOS PR #379
merge commit: c064c7542e113703a9fd0efe9eb08106de956937
```

The current-iPhone bootstrap retains the verified `signedIpa` in the same invocation, builds the existing secret-free TVC upload descriptor, sends the bytes to the TVC byte-ingress endpoint using `application/octet-stream`, `credentials: "omit"`, `cache: "no-store"`, and validates the returned native Build Upload result and TVC byte-ingress receipt.

The source-defined success state is now:

```text
TVC_NATIVE_BUILD_UPLOAD_COMMITTED
```

Its source-declared next boundary is:

```text
TESTFLIGHT_PROCESSING_INSTALL_OBSERVATION
```

Neither string is runtime evidence merely because it exists in source.

### Site projection and live publication

```text
StegVerse-Labs/Site PR #1299
merge commit: 6c1f267b49ab6e36618a2eccc8afceaf4544fbe0
handoff reconciliation: Site PR #1302 @ 39897d784922c8e1dc1eb3ddda6c82a6bf256753
claim terminalization: Site PR #1303 @ 61867fa9222a166cfff0a20b2153b146aa506344
```

Exact-head governing Site checks passed, including Handoff Orchestrator run `34791706184`, Heartbeat run `34791706250`, and Site Bootstrap Validate run `34791706246`.

Credential-free live publication proof run `34791777867` fetched the public bootstrap, upload-request builder, and byte-ingress client and required the exact native-upload markers. It completed PASS with:

```text
TASK0011_NATIVE_TESTFLIGHT_UPLOAD_PUBLICATION=PASS
TASK0011_RUNTIME_PROOF_EFFECT=NONE
```

Therefore the source and live public projection are established, but no Apple provider execution, native Build Upload, TestFlight processing, installation, or resident runtime state is inferred from those facts.

## Current first unresolved predicate

```text
TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED
```

All known machine-owned source-composition gaps on the same-device path are now satisfied. Remaining Goal Task-specific predicates are:

- authentic same-device current-iPhone execution;
- Device->KV Interlock/InTr admission and verified KV state for that execution;
- authentic TV/TVC signing/provider/native Build Upload state transition for that execution;
- final TestFlight processing/release/install observation;
- retained same-device StegOS/StegBrowser runtime observation;
- Master Records custody acceptance and same-execution reconstruction;
- return to the frozen global runtime measurement with authentic evidence only.

## Next admissible work

Continue through the existing public same-device runtime surface. Preserve the exact successful result or exact fail-closed result. A valid execution may now progress to `TVC_NATIVE_BUILD_UPLOAD_COMMITTED`; if it does, that observed result must still be followed by the required TestFlight processing/install observation. Classify any authentic failure by its owning reusable component and repair only that owner/component when machine-admissible. Do not add parallel transport/session/adapter/retry/custody machinery, synthesize evidence, require a second user-operated device, or introduce device-local user verification.

## README state

The `.github` root README already contains the canonical Reusable Task Component Model projection from PR #1652. This source-state reconciliation does not materially change repository-wide function. No additional README mutation is required.

## Manual work

On the established current iPhone, open `https://stegverse.org/task0011-same-device-kv-recovery.html`, tap `Use This iPhone's KV and Prepare IPA`, and preserve the exact displayed result or exact fail-closed message. Do not clear Safari/site/KV/node continuity state and do not switch devices. If the page specifically reports `resident KV installation not verified`, use `Admit Existing KV Installation Receipt` only if the canonical `_System/installation.receipt.json` is available.
