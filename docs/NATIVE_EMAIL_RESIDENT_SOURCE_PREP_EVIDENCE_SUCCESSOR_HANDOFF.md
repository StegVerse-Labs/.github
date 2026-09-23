# Native Email Resident Source-Prep Evidence — Successor Handoff

Parent Goal Task ID: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
Parent COSV: `10100000100000`
Canonical source-prep WorkerCoordinator task: `SV-DN1-PRODUCTION-SOURCE-PREP-001`
Source-prep COSV: `50000000102000`
Handoff kind: **bounded phase successor of the same parent Goal**, not a new task/worker/authority owner.
Predecessor handoff: `docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md`
Predecessor documented Goal Prompt Count: **20/20**
Task Registry generation observed at phase creation: **204**; re-read canonical main before any transition or mutation.
State: `SOURCE_REPAIRS_MERGED__AUTHENTIC_RESIDENT_EXECUTION_NOT_ACCESSIBLE`.
Authority effect: **NONE**.

## Decision at the original 20-prompt boundary

The original Goal is **not complete**, checked out, or terminal. Retain its canonical task ID, COSV, existing Healer standing resident request, targeted WorkerCoordinator task, Interlock/InTr boundaries, TV/TVC credential ownership, and Master Records reality requirements unchanged. This document starts a new **bounded evidence-consumption phase** under the same owner. Do not mint a separate Goal, machine-owned dispatch request, scheduler, executor, authority plane, resident device prerequisite, or duplicate remediation task to represent a missing authentic observation.

## Exact existing execution path

```text
SHWP-HEALER-SOVEREIGN-SCHEDULER-001 (standing resident request)
-> existing resident Healer/source-refresh bridge
-> StegVerse-Healer reusable_task_scheduler.py
-> targeted .github/scripts/refresh_and_execute_resident_task.py
-> SV-DN1-PRODUCTION-SOURCE-PREP-001 (independent WorkerCoordinator claim/fence)
-> process:sv-dn1-production-source-prep-v1
-> existing current-identity source-prep worker
-> ~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json
-> existing Healer _verified_governance_component_roots() readback
-> only after verified predicate 1: existing TV/TVC Gmail owner-session observation
```

Do **not** substitute source-merge state, CI, GitHub Actions, Site projection, a synthetic response, a copied documentation example, or a missing GitHub receipt path for the authentic resident cycle. Do not repeat GitHub-only receipt searches absent a newly exposed authentic runtime artifact.

## Merged path repairs already closed

- Healer PR #98, merge `eb0af12746b26fec205e3e8cd39326f63c0550d8`: if source-prep v2 receipt is unavailable, call the already-existing targeted resident bridge instead of only reading an absent receipt.
- .github PR #2559, merge `b639686c19167557957ebf17e89b6e9ce1c65702`: retain `SV-DN1-INTR-RUNTIME-001` as provenance parent while marking `runtime_predecessor_reconstruction_required=false` for independently admitted source preparation with `dependencies=[]` and `upstream_runtime_dependency=null`.
- Healer PR #101, merge `8a7e64b5c41ef093eb509ea9956d422e500e1614`: require canonical source-prep task/worker identity, exact claim/fence binding and current-source-identity proof during readback.

Source tests and merges establish source readiness only. At handoff creation no genuine post-repair resident claim, fence, full target result, or completed source-prep v2 receipt was accessible through the available GitHub connection; absence from GitHub does not establish non-occurrence on the sovereign resident filesystem.

## First unmet predicate: authentic resident source preparation

Consume exactly one authentic post-repair targeted WorkerCoordinator result and the corresponding retained **same-invocation** bound-state source-prep receipt, then require all of:

1. Real current resident source refresh and independently authorized WorkerCoordinator `SV-DN1-PRODUCTION-SOURCE-PREP-001` claim. Nonempty authentic `claim_id=SHWP-SV-DN1-PRODUCTION-SOURCE-PREP-001-G<fencing_token>` and fresh integer `fencing_token>22`, bound to the same target result and receipt.
2. Receipt schema `stegverse.sv-dn1.production-source-prep-receipt/v2`; exact task/worker; `state=COMPLETE`; transition `SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE`.
3. Exactly four canonical source roots **and** source identities for `stegverse.sdk`, `stegverse.stegcore`, `stegverse.core-lite`, `stegverse.master-records`. Verify each actually materialized current root and its `sha256-content-manifest` identity; `source_identity_scheme=sha256-content-manifest`; `migration_anchors_verified=true`; `current_source_identity_verified=true` and scheme `sha256-content-manifest` where emitted.
4. `network_source_fetch_performed=false`, `github_platform_required=false`, `credential_used=false`, `github_token_used=false`, `repository_writeback_performed=false` and no secretly introduced source/platform transport.

If an **authentic** targeted result reveals a first real existing-path defect in refresh, admission, claim/fence, worker execution, bounded-state commit, or same-invocation readback, repair **only that defect** under the current canonical Task Registry generation and existing source owner. If runtime access is unavailable, preserve `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` and do not make a speculative source repair or manufacture a receipt.

## Downstream gate and completion

Only after the above authentic evidence proves native-email completion predicate 1 may the existing TV/TVC Gmail owner-session observation proceed. Do not claim a Gmail session, KV exact-byte persistence, governed archive, Master Records closure, inbox-empty state, or task completion on this phase's document publication. Preserve the parent task's remaining original completion chain from the predecessor handoff.

No second device, remote-connected device, manually maintained carrier, new resident runtime, scheduler, dispatcher, WorkerCoordinator, credential route, source installer/transport, authority plane, custody store, or Site runtime role is authorized.

## Bounded successor phase acceptance

This handoff is durable and cross-session addressable when referenced from the original Goal handoff and canonical task record without changing that record's `PROPOSED/UNCLAIMED` coordination state. It is evidence-phase documentation only. One source-repair task remains the same original Goal until an **authentic** new independent scope is demonstrated and separately admitted through canonical Task Registry/COSV.

## 2026-09-23 first source-proven replay-seam repair candidate

Canonical Task Registry generation at code review: **205**. The parent Goal remains `PROPOSED / UNCLAIMED`; no runtime state was promoted.

Tracing the exact existing standing-Healer -> `refresh_and_execute_resident_task.py` -> WorkerCoordinator lane revealed a **source-proven evidence discontinuity**: before this repair the bridge persisted its `stegverse.resident-refresh-targeted-execution/v3` latest + immutable receipt only after local source refresh, exact COSV pointer validation, preflight and subprocess return. An exception in those earlier steps exited without an attempt/failure receipt, making the first failed transition unreplayable from this bridge even when the process really ran. This is a source defect, not an assertion that an authentic resident failure has happened.

The bounded repair uses only the existing bridge and its existing `receipts/sovereign-host/resident-targeted-execution.latest.json` plus immutable by-content receipt surfaces. The same function now retains a fail-closed `state=BOUNDARY_FAILED` receipt on an actual thrown exception, identifying `failed_transition_boundary` / `next_replay_boundary` and exception class but not carrying exception messages, process stderr, credentials, or presumed execution/custody success. Instrumented stages: `LOCAL_SOURCE_REFRESH`, `COSV_POINTER_VALIDATION`, `EXISTING_CLAIM_PREFLIGHT`, `TARGETED_ENTRYPOINT_RESOLUTION`, `TARGETED_ENTRYPOINT_VALIDATION`, `EXISTING_CLAIM_CARRIER_VALIDATION`, `TARGETED_WORKER_SUBPROCESS`. This envelope grants no execution authority, never mints a claim/fence, never claims WorkerCoordinator completion, and remains outside Master Records custody or Interlock/InTr transition authority. Actual resident process execution is required to issue authentic runtime evidence.

Focused regression tests exercise local refresh failure, COSV validation failure, and a subprocess timeout; each requires immutable replay-boundary retention and **no fabricated claim/fence or completion**. The genuine registered runtime/organization-level worker transition and Master Records failure/expiry chain remain separately authoritative; do not mistake this boundary receipt or CI for their closure. If existing bound-state, worker, or organization receipts reveal a later fault, reconcile them against the exact preceding valid stage, and repair the first actual failing boundary only.

The source-repair candidate does not satisfy the original source-preparation predicate. After merge, require a real post-repair targeted WorkerCoordinator result, matching claim/fence, and completed same-invocation four-root v2 receipt before advancing TV/TVC Gmail owner-session observation.
