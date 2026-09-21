# SDK Four-Stage Evidence Remediation Mirror Handoff

Updated: 2026-09-21
Goal Task ID: `SDK-FOUR-STAGE-EVIDENCE-REMEDIATION-001`
Parent Goal Task ID: `SDK-FOUR-STAGE-POST-LINEAGE-EVIDENCE-PACKAGE-001`
COSV ID: `71000000111111`
Status: ACTIVE / CHECKED_OUT

## Purpose

Repair only the Option-A four-stage SDK evidence defects established by the validated v2 review. Preserve `SDK-FOUR-STAGE-POST-LINEAGE-EVIDENCE-PACKAGE-001` as immutable RETIRED / COMPLETED / VALIDATED history. This task does not retroactively invalidate the retained package's reproducibility or lineage evidence; it narrows overclaims and makes future experiment predicates falsifiable and externally defensible.

## Canonical review reconciliation

Confirmed against current `StegVerse-org/StegVerse-SDK` main:

- F1: Task-4 overlap observation is non-falsifiable because `execution_started_ns` is captured before the invocation barrier.
- F2: current "partitions" are whole-payload tagged replicas rather than disjoint decomposition.
- F3: standing, retirement, and portions of group binding are derived/local-semantic observations rather than independent retained runtime facts. Retained-standing and retirement proof is explicitly out of this Option-A implementation scope and must become a separate successor Goal Task.
- F4: `_LOCAL_SEMANTIC_WORKER_BINDINGS = set()` leaves the governed-runtime/local-semantic completion guard inert.
- F5: Test 3 does not differentially compare Test 2 and Test 3 modulo preregistered identity fields.
- F6 correction: preregistration was anchored before attempt 2. Canonical coordination commit `0127082e415fb220c709962ab7d0645e06105a4c` records PDF SHA-256 `37363e0d3d8880956b0e97a90c54a140e6bebfac0aa9be73a5fb90ab2effa5d7`; GitHub records that commit at 2026-09-21T00:42:26Z and attempt-2 execution beginning at 2026-09-21T00:42:35Z. Remaining provenance work is to retain/disclose attempt-1 disposition and make raw evidence/exhibit inventory complete and accurate.

## Option-A implementation predicates

1. Move the Task-4 measured execution start to the true post-invocation-barrier work interval and add a serialized negative control that must not report overlap.
2. Replace tagged whole-payload "partition" behavior with genuine deterministic disjoint partitioning and explicit reconstruction/coverage proof, or explicitly relabel the operation as replication. Prefer genuine deterministic partitioning when it preserves the generic processor contract without test-specific logic.
3. Replace tautological group-result binding with recomputation and equality validation over the exact per-worker result bindings.
4. Populate and enforce the SDK-local semantic binding set so any route declared `STEGAGENTS_GOVERNED_RUNTIME` cannot terminate through a local-semantic processor. The local semantic experiment must declare/use a non-governed local-semantic routing surface rather than bypassing this boundary.
5. Add Test-2/Test-3 differential invariance assertions modulo explicitly enumerated identity/proposition fields and preserve lifecycle phase-order assertions for both.
6. Repair stale workflow identity comments, attempt-1 disposition/provenance disclosure, exact-exhibit wording, raw-log/inventory completeness, environment capture, and processor-request inventory where applicable.
7. Exact-head validation must pass before merge. No runtime, deployment, retained-standing, retirement, Master Records, HB, or authentic-governed-execution claim may be inferred from local-semantic CI.

## Separate successor boundary

After Option A is merged and validated, derive a separate Goal Task for custody-gated retained standing/retirement proof: externally established lease/fence, retained activation custody, admission conditioned on that custody, and an authentic refused post-close invocation using the stale fence. HB may stamp chronology but remains non-authorizing.

## Generation fence

Registration read canonical Task Registry generation 177 and advances this branch to generation 178.


## Completion — 2026-09-21

Option A is complete and validated.

- SDK PR #304 merged as `e1116e9cb5f5043c9198505d64560b710c517e88`.
- Exact validated head `0bc31804750c224257409e2774fe918e3c797c10` and merged main share exact tree `f42bb1017aa6f7bb185ba410d8ddca369524b77a`.
- Four-stage validation run `35648276053` PASS.
- Artifact `10661081336`, SHA-256 `82fd8e824fe5fb175ae17fc57ea34a729996dd37b02878b11969f10abcd93ba5`.
- All 13 triggered SDK exact-head workflows passed.
- Coordination registration PR #2498 merged as `878856553d5a06e6418a0b968a88d6d75d32a38c`.
- Historical F6 correction remains: preregistration was anchored by commit `0127082e415fb220c709962ab7d0645e06105a4c` before attempt 2; attempt 1 disposition was SUCCESS.

Status is now RETIRED / COMPLETED / VALIDATED.

Separate successor: `SDK-FOUR-STAGE-RETAINED-STANDING-RETIREMENT-PROOF-001`, handoff `docs/SDK_FOUR_STAGE_RETAINED_STANDING_RETIREMENT_PROOF_MIRROR_HANDOFF.md`.
