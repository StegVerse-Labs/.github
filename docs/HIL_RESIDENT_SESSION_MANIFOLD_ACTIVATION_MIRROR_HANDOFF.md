# HIL Resident Session Manifold Activation Mirror Handoff

Updated: 2026-09-08
Repository: `StegVerse-Labs/.github`
Issue: `#1178`
Goal: `HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001`

## Source of truth

This file is the canonical continuation record for materializing the already-defined HIL resident session cohort through the governed manifold orchestration pattern.

Inherited canonical sources:

- `docs/HIL_RESIDENT_SESSION_COHORT_MIRROR_HANDOFF.md`
- `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`
- `docs/GOVERNED_MULTILANE_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`
- `docs/CROSS_TASK_COORDINATION_MIRROR_HANDOFF.md`
- `scripts/dispatch_resident_execution_requests.py`
- `scripts/run_worker_runtime.py`

## Current continuation state

- PR `#1179` remains OPEN and unmerged.
- README completeness is already committed and remains `NO README CHANGE REQUIRED / EXISTING DOCUMENTED SOURCE-REFRESH CONTRACT` unless later remediation changes externally meaningful semantics.
- The three previously active COSV gaps are closed through their existing evidence-backed vectors.
- Corrected aggregate COSV index blob `53bb6d7e9cfe4e53b6c843de1b12d93fa16c2297` containing 93 aggregate rows is attached to `control/task-vector-index.json` on the feature branch by commit `4a847584ccb95f8dbd33e92a3e2b2cf2a97be18e`.
- Exact merge-ref diagnostics at that head observed the corrected live worker projection: `88` unique worker task IDs / `81` canonically indexed worker task IDs, with zero active unindexed workers and the seven remaining unindexed IDs all terminal historical/superseded.
- The diagnostic repair candidate for `control/cosv-global-registry-coverage.json` must be attached after branch reconciliation with current `main`, so the branch and PR merge ref use the same denominator source graph.
- Obsolete fixed-count worker denominator assertions were removed in commit `369dda428b6866ad5c39fd26b0eaae27c405ec1d`; remaining historical tests that count only aggregate rows must be reconciled to the aggregate+shard effective-index model.
- `main` continued advancing during remediation; exact collision reconciliation against the newest `main` is required before final exact-head validation.
- Runtime HIL activation/transport proof remains intentionally pending authentic resident execution evidence and is not satisfied by source validation or GitHub Actions.

## Governing objective

Visit the existing HIL resident-session cohort in one bounded manifold execution while preserving each task's independent authority, request identity, claim/fence, evidence, completion predicate, and retry semantics.

```text
one manifold visit
!= one shared authority
!= one shared claim/fence
!= one shared completion predicate
```

No second runtime, dispatcher, WorkerCoordinator, scheduler, heartbeat, oscillator, credential route, transition authority, or second user-operated machine is created or authorized.

## Declared lineage

Machine-readable lineage:

`control/manifold-lineage.d/hil-resident-session-manifold-activation-001.json`

Declared nodes:

- `SHWP-HIL-SOVEREIGN-RECEIVER-001` — invoke existing resident request consumer selector `hil`.
- `COSV-LIVE-PACKET-AUTOMATION-006` — visit existing WorkerCoordinator task.
- `SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001` — visit existing WorkerCoordinator task.
- `SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001` — visit existing WorkerCoordinator task.
- `SHWP-TV-TVC-RESIDENT-PROOF-001` — visit existing WorkerCoordinator task.
- `SHWP-DURABLE-RUNTIME-ACTIVATION` — invoke existing resident request consumer selector `g18`; HIL does not inherit G18 authority or depend on G18 terminalization.
- `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` — invoke existing resident request consumer selector `ecosystem_chat`; retain the dedicated Ecosystem Chat parent semantics.

## First actionable HIL predicate

The HIL lane remains subject-bound to:

`PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`

The manifold does not satisfy this predicate by visiting adjacent lanes. Only the existing HIL request consumer may produce qualifying consumption evidence.

## Execution contract

Standing request:

`control/resident-execution-request.d/hil-resident-session-manifold-activation-001.json`

Resident consumer:

`control/resident-execution-request.d/consume-hil-resident-session-manifold-activation.py`

The consumer:

1. validates the exact declared lineage and non-authorizing request;
2. uses the existing exact-selector resident dispatcher for request-specific lanes;
3. uses the existing WorkerCoordinator runner for ordinary registered task lanes;
4. continues visiting later independent lanes after a task-local wait/failure;
5. writes one aggregate visit receipt without promoting any child to complete;
6. preserves TV/TVC credential authority, GitHub-token runtime authority NONE, HB non-authority, and no-second-machine semantics.

## Resident source-refresh parity repair

Preflight found that the existing umbrella manifold consumer requires static inputs under:

- `control/manifold-lineage.d/`;
- `control/task-vector-index.d/`;
- `data/canonical-task-records/`.

The canonical local-only WorkerCoordinator source refresh did not carry those directories. The existing refresh and its base copy are therefore extended to carry those static coordination inputs while continuing to exclude mutable runtime state, network fetch, credential acquisition, or repository mutation.

This is a dependency-completeness repair of the existing resident source-refresh contract, not a new runtime or authority plane.

## README completeness determination

`NO README CHANGE REQUIRED / EXISTING DOCUMENTED SOURCE-REFRESH CONTRACT`.

Evidence-supported basis: `README.md` already documents the externally meaningful local-only WorkerCoordinator source-refresh contract—canonical static dependency propagation, no network fetch or credential acquisition, no second carrier/worker/scheduler, preservation of mutable runtime state, and no inference of runtime execution from refresh. The three newly carried directories are static canonical coordination dependencies required by the already-merged manifold consumer. Their inclusion restores dependency parity without changing the documented authority model, external interface, credential behavior, second-machine requirement, or execution semantics.

This determination follows the same documented parity rule already used for omitted resident self-heal/source-refresh dependencies. If the change expands beyond static dependency parity, README impact must be re-evaluated before merge.

## Completion boundary

Source completion requires:

- exact lineage and standing request;
- resident consumer materialized on the existing WorkerCoordinator surface;
- resident source refresh carries the static lineage/task-record inputs required by the umbrella and nested manifold consumers;
- deterministic tests proving lane identity, selector mapping, no authority merge, continued visitation semantics, and source-refresh parity;
- corrected aggregate COSV index and live worker coverage projections attached to the branch;
- branch validation and collision review against current `main`;
- exact-head organization-control and Heartbeat validation green before merge.

Runtime completion remains separate and requires authentic child-produced receipts. The manifold itself grants no activation authority.

## Remaining destinations after authentic activation/release

Only after owning release predicates qualify, verify pertinent propagation to:

- `StegVerse-Labs/Site`
- `GCAT-BCAT-Engine/Publisher`
- `StegVerse-Labs/admissibility-wiki`
- `StegVerse-002/stegguardian-wiki`
- `StegVerse-Labs/Sit` only after repository identity/role is independently verified.
