# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-10

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / EXACT CURRENT-IPHONE KV PROJECTION ARTIFACTS VALIDATED / TASK-2026-0010 ALLOCATOR WRAPPER REPAIRED+PUBLISHED / AUTHENTIC ALLOCATION RETRY NEXT`

## Canonical architecture

KV remains the private governed continuity boundary. Device/browser presentation is interchangeable and ephemeral after continuity proof. Interlock/InTr owns transition/admission; WorkerCoordinator owns claim/fence authority; TV/TVC owns credential/provider authority; HB is observability only; GitHub Actions are validation/evidence transport only.

```text
current iPhone
-> Device→KV Universal InTr
-> CURRENT_IPHONE_TESTFLIGHT_SIGNING admission
-> verified KV installation
-> same-lineage browser capability observation
-> opaque KV projection
-> StegOS projection consumer
-> canonical TASK-2026-0010 allocation/fence
-> Site TestFlight bootstrap projection
-> TV/TVC provision/sign/upload
-> TestFlight install
-> retained StegOS/StegBrowser observation
-> one frozen global measurement pass
```

## Proven implementation/runtime state

Merged source:
- KV producer: `continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`.
- StegOS consumer: `StegOS#314` -> `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`.
- Site Device→KV projection adapter: `Site#1178` -> `3da593a61a536a625fcea4a26df8d1f491f00b44`.
- Safari resident-KV recovery: `Site#1197` -> `bd4c64a4dfa8130d3b8c015a242fbab5afc67fa1`.

Authentic current-iPhone Safari crossed the initial resident-KV failure and reached `PROJECTION_CONTEXT_READY` for `CURRENT_IPHONE_TESTFLIGHT_SIGNING` with `entry_state=ADMITTED` and `browser_capability_state=OBSERVED_COMPATIBLE`.

Two exact downloaded projection artifacts were retained and independently checked against the merged StegOS projection validator:

```text
primary bytes: 620
primary sha256: 93caa302f310be097005c21639504bc13a7e8090d161d56cd0823c37363db3f8
repeat bytes: 620
repeat sha256: 064c8fcac9e1ee87c6f6dc73807689fded772865ae4b3f461b304d26aaf7df64
schema: stegos.kv-bound-ephemeral-projection-context/v1
purpose: CURRENT_IPHONE_TESTFLIGHT_SIGNING
entry_state: ADMITTED
browser_capability_state: OBSERVED_COMPATIBLE
persistence_effect: NONE_EPHEMERAL_CONTEXT_ONLY
authority_effect: NONE_PROJECTION_GATE_ONLY
```

The different KV-transition/admission commitments across the two artifacts are retained as separate admitted-run evidence; the browser-capability commitment is stable across both. The primary unsuffixed artifact is the continuation artifact; the suffixed artifact is repeat evidence.

## Authentic allocator observation and remediation

Canonical `TASK-2026-0010` is queued to project the exact StegOS current-iPhone TestFlight bootstrap into Site under a fresh allocator fence.

The first current-iPhone allocator attempt verified the established StegOS node continuity, then failed before mutation with:

```text
FAIL_CLOSED: auto-execution requires exactly one queued canonical successor
mutation_performed: false
```

The canonical allocator supports multiple queued tasks and owns deterministic ordering/selection. The false restriction existed only in Site's auto-execution wrapper. `Site#1205` repaired the wrapper so it now requires:

```text
TASK-2026-0010 is present in receipt.queued
AND
receipt.selected == TASK-2026-0010
```

It still fails closed if the canonical allocator selects another task. No allocator ordering, dependency, conflict, CAS, claim/fence, HB, credential, or runtime authority was widened.

`Site#1205` merged at `281bcb0c56d84eef933e57a21f6ed1ef91660dfb` after exact-head Site Handoff, Site Bootstrap, Ecosystem Heartbeat, and StegOS Node Public Observation checks passed. The repair was published through Site Pages. Claim-only `Site#1206` subsequently merged at `66c30c269d546520e75fa65a50c912a076ea7b6e` after its corrected terminalization checks passed.

## Current first unresolved predicate

`AUTHENTIC_CURRENT_IPHONE_TASK_2026_0010_CANONICAL_ALLOCATION_RETRY_AND_CLAIM_EVIDENCE`

Required evidence:

```text
established current-iPhone node continuity remains verified
canonical allocator queue contains TASK-2026-0010
canonical allocator selects TASK-2026-0010
atomic retained-state transition commits
fresh claim/fence is emitted
exported same-device allocator evidence is retained exactly
```

No Site TestFlight product-path mutation is authorized until that fresh claim/fence is authentically observed.

## Next execution sequence

1. Re-open `https://stegverse.org/stegos-node/org-allocator-bootstrap-auto.html` on the current iPhone in Safari.
2. Require canonical selection of `TASK-2026-0010`; do not force selection if another task wins.
3. If successful, export and retain the exact allocator evidence JSON.
4. Bind the authentic claim/fence to `claim/current-iphone-testflight-static-bootstrap-r1` and re-observe Site `main`.
5. Project the exact StegOS successor assets into the claimed Site branch and verify source hashes/bytes.
6. Validate/merge Site projection and update successor lineage.
7. Feed the primary exact KV projection to the published StegOS TestFlight bootstrap, then continue TV/TVC provisioning, ephemeral same-device signing, same-session verification, native Build Upload, TestFlight install, retained-node observation, and one frozen global measurement pass.

## README impact

No new `.github` product semantics were introduced by this reconciliation. Site functional work maintained its repo-local handoff and tests.

## Manual work

On the current iPhone in Safari, open `https://stegverse.org/stegos-node/org-allocator-bootstrap-auto.html`. If it reports `Canonical allocation auto-executed: TASK-2026-0010`, export the exact allocator evidence JSON and return it. If it fails closed, retain the exact displayed result; do not reset allocator or browser state.
