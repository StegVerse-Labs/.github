# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
Historical implementation PR: `StegVerse-Labs/.github#1344`
Substrate-registration enforcement PR: `StegVerse-Labs/.github#1539`
Merged substrate-registration enforcement: `bbe00e1a1382ea8c98ae6441ff3b33f01dacc6d6`
Status: `RETIRED / COMPLETED / GENERATION FENCE MERGED+VALIDATED / USER-ACTION-SURFACE COLLISION MERGED+VALIDATED / NO SUCCESSOR REQUIRED`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition from current canonical coordination state. New runtime-capable task registrations must also resolve execution-substrate dependencies before a reachability/evidence gap can be promoted into an external-device requirement.

Task Registry sorting is coordination only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Canonical dispositions

- `CONTINUE`
- `COORDINATE_CONVERGENCE`
- `STOP_COLLISION`
- `STOP_SUPERSEDED`
- `STOP_INACTIVE`
- `STOP_NOT_REGISTERED`
- `STOP_SUBSTRATE_REVIEW_REQUIRED`

## Execution-substrate registration invariant

Every newly registered runtime-capable canonical task must review these substrates in this order:

1. `STEG-BROWSER-RETAINED-RESIDENT-NODE`
2. `STEGOS-CURRENT-DEVICE-NODE`
3. `STEG-BROWSER-EPHEMERAL-LEASE`
4. `SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER`
5. `ADMITTED-EPHEMERAL-STEGOS-NODE`
6. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT`

The task record uses `execution_substrate_resolution` / `stegverse.execution-substrate-resolution/v1` and must preserve:

```text
second_user_operated_device_allowed=false
authority_effect=NONE
```

A review with `limitation_class=EVIDENCE_REACHABILITY` may be `PENDING_EVIDENCE`; it may not be `UNSUITABLE`. Therefore an empty Remote Computer inventory, unavailable connector, missing receipt, temporarily unreachable listener, or equivalent observation cannot itself become a hardware requirement.

`external_device_required=true` is valid only after every preceding single-device substrate is evidenced `UNSUITABLE` or `NOT_APPLICABLE`, and the external substrate is explicitly selected. Any `UNSUITABLE` determination requires evidence references.

## Merged implementation — PR #1539

Validated PR head:

`7e68c906381d97e7f4ebf9e86593c447caede414`

Squash merge:

`bbe00e1a1382ea8c98ae6441ff3b33f01dacc6d6`

Merged surfaces:

- `scripts/validate_task_registration_substrate_resolution.py`
- `scripts/validate_org_control_plane.py`
- `schemas/canonical-task-record.schema.json`
- `tests/test_task_registration_substrate_resolution.py`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `tests/test_task_registry_collision_checkin.py`
- `.github/workflows/org-control-plane-validate.yml`

The organization-control workflow now triggers directly on `data/canonical-task-records/**`, so a task-record-only registration cannot bypass the substrate gate.

The registration validator inspects newly added canonical task records relative to the PR base. Legacy records remain readable; new runtime-capable registrations cannot omit substrate resolution.

The collision evaluator now:

- validates present `execution_substrate_resolution` before continuing;
- emits `STOP_SUBSTRATE_REVIEW_REQUIRED` on invalid substrate review;
- projects `selected_execution_substrate` into the check-in disposition;
- treats a shared selected substrate as a `COORDINATE_CONVERGENCE` signal;
- does not treat substrate sharing alone as a hard collision.

This lets multiple tasks converge on one eligible retained StegBrowser/StegOS resident rather than independently inventing listeners, activation pages, connector requirements, or second-device assumptions.

## Exact-head validation

All required exact-head lanes passed at `7e68c906381d97e7f4ebf9e86593c447caede414`:

- organization control: run `34667518970` — PASS;
- deterministic repository suite: run `34667519006` — PASS;
- Heartbeat validation: run `34667518973` — PASS.

Within organization control, step `Test task registration substrate sorting invariant` passed explicitly.

Regression coverage includes:

- retained StegBrowser resident selected first;
- runtime-capable registration without substrate review rejected;
- `EVIDENCE_REACHABILITY -> UNSUITABLE` rejected;
- premature external-device selection rejected;
- external-device selection accepted only after evidenced same-device exhaustion;
- legacy/non-runtime compatibility;
- substrate-aware check-in convergence without converting shared substrate into a hard collision.

## Existing collision enforcement

The pre-existing anti-collision implementation still provides:

- canonical task identity/supersession resolution;
- repository/component/lineage/adjacency overlap detection;
- recent check-in/check-out event-history participation;
- canonical Work preflight before mutation;
- portable WorkerCoordinator preclaim gating;
- hash-bound check-in context/disposition evidence;
- fail-closed non-`CONTINUE` portable checkout behavior.

## Remaining defect: user-action/runtime surface collisions

Issue #1343 records a remaining distinct gap: mutable human/browser action surfaces are not yet first-class collision resources. Multiple tasks were able to independently request the same current-iPhone URL/runtime surface because URL/browser/service-worker/action identity was not part of registry overlap sorting.

GADI/HIL exposed this defect. This remains owned by the same anti-collision goal; do not create a second collision engine.

Next implementation must add structured user-action surface identity to registration/check-in so the registry can detect overlap across at least:

- exact URL/route;
- current-device/browser context class;
- service-worker/runtime surface;
- action type;
- owning task/request identity;
- shareable vs exclusive semantics.

The registry must return `COORDINATE_CONVERGENCE` or `STOP_COLLISION` before user instruction when two tasks target an incompatible shared action surface.

## Canonical files

- `data/canonical-task-records/TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001.json`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/validate_task_registration_substrate_resolution.py`
- `scripts/task_registry_checkin_event_history.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `workercoordinator/portable_checkout.js`
- `schemas/canonical-task-record.schema.json`
- `tests/test_task_registry_collision_checkin.py`
- `tests/test_task_registration_substrate_resolution.py`
- `tests/test_portable_workercoordinator_registry_gate.py`

## Manual work

None.


## Repository-only current-record scope distinction — 2026-09-17

`HYGIENE-CAUSAL-ROOTS-001` exposed a bounded false-convergence case in the existing general evaluator. The current-record overlap function treated any shared repository target as sufficient for `COORDINATE_CONVERGENCE`, even when both canonical tasks declared non-empty, disjoint component scopes and had no lineage, adjacency, or shared selected execution substrate. The existing `checkin_context` could add intended repositories/components but could not narrow the task's full declared repository set, so the four hygiene overlaps remained blocking despite explicit component separation.

The existing evaluator is repaired in place; no second collision engine or authority plane is introduced. For current canonical registry rows only, repository overlap is retained as visible non-authorizing evidence but classified `DISTINGUISHED_COMPONENT_SCOPE / blocking=false` when all of these are true:

- at least one repository overlaps;
- component intersection is empty;
- both tasks declare non-empty component scopes;
- the declared component scopes are disjoint;
- no task lineage overlap exists;
- no adjacency exists;
- no shared selected execution substrate exists.

Every stronger signal remains collision/convergence evidence. Repository-only overlap also remains conservative when either task lacks component scope. Recent returned/stopped session history is unchanged and remains repository-or-component conservative because historical event context is a different evidence class and must not be weakened by this repair.

The disposition now preserves nonblocking current-record distinctions separately as `repository_only_scope_distinctions`; they are not silently discarded and do not enter `collision_candidates`. WorkerCoordinator claim/fence authority, Interlock/InTr transition authority, TV/TVC credential authority, Master Records reality authority, and the existing fail-closed requirement that Canonical Work proceed only on exact `CONTINUE` remain unchanged.

Focused regression coverage extends `tests/test_task_registry_collision_checkin.py` and requires the four current hygiene repository-only overlaps to remain visible as scope distinctions while the isolated hygiene preflight reaches `CONTINUE`. It also preserves the fail-closed requirement when component scope is missing.


## Session coordination generation fence — 2026-09-18

This continuation first re-read current GitHub `main`, the canonical Task Registry, this handoff, and the existing anti-collision implementation. The observed authoritative base was:

- GitHub `main`: `badb24754a31f2d7e061c10f900209954afd9719`;
- canonical Task Registry generation: `41`;
- this Goal's canonical shard: `ACTIVE / CHECKED_OUT`;
- this Goal was present as a canonical shard/handoff but absent from the monolithic registry projection, so this change registers the existing identity there rather than minting a replacement task.

The bounded repair advances the proposed monolithic registry generation to `42` and makes that monotonically increasing generation an explicit session-mutation fence on the already-canonical check-in path.

Every admitted production caller of `scripts/evaluate_task_registry_collision_checkin.py` must now carry `observed_registry_generation`. Before task lookup, collision sorting, WorkerCoordinator consideration, route installation, or other Canonical Work mutation:

- missing observation -> `STOP_COORDINATION_GENERATION_REQUIRED`;
- observed generation lower than current -> `STOP_STALE_COORDINATION`;
- observed generation higher/divergent from current -> `STOP_COORDINATION_GENERATION_MISMATCH`;
- only an exact generation match remains eligible for ordinary collision evaluation.

A stopped or stale session is explicitly non-admissible for:

- source writes;
- pull-request create/update;
- pull-request merge;
- new handoff claims.

Its only admissible next action is to re-read current GitHub `main`, the current canonical Task Registry generation, and the applicable mirror handoff, then perform a fresh check-in.

The existing Canonical Work selector and bootstrap now carry the exact generation they just read into the check-in request, so a resident/local projection that has advanced or diverged fails closed rather than silently continuing from older coordination state. The AI-session gate passes the same request through to the canonical evaluator; missing/stale generation therefore stops before canonical mutation.

This is a coordination fence, not a new execution fence. WorkerCoordinator remains execution claim/fence authority; Interlock/InTr remains transition authority; Master Records remains observed-reality/reconstruction authority; TV/TVC remains credential authority.

### Platform-enforcement boundary

The repository's current GitHub `main` branch is not protected by an active required-status/ruleset gate. Therefore this source change does **not** claim that GitHub itself can prevent an administrator or other out-of-band actor from directly bypassing canonical tooling. It does make stale-session mutation fail closed on the canonical Task Registry/Canonical Work paths. Platform-level prevention of arbitrary GitHub bypass would require repository ruleset/branch-protection administration in addition to this source fence.

### Validation target

Before merge, require focused stale/current-generation regression tests plus the normal organization-control, deterministic repository, and Heartbeat validation lanes. After merge, re-read `main` and require Task Registry generation `42` plus this handoff before treating the fence as canonical.


## User-action/runtime-surface collision enforcement — 2026-09-18

This continuation re-read current GitHub `main`, the canonical Task Registry, and this handoff before further mutation. The authoritative base had advanced from generation `42` to generation `45` at `3ad023ab017e5e7a266d2c4139fedc18c4c76d9c`, so the pre-existing action-surface branch was stale under the merged generation fence. It was reconciled before new writes by creating merge commit `93c265b59196a6ff1cf744f9581944ceea6ddcd1` with current main plus the already-authored evaluator change; the evaluator mutation was preserved rather than independently reimplemented.

The branch now proposes registry generation `46` and extends the existing collision engine only. No second collision engine, scheduler, dispatcher, claim/fence authority, transition authority, credential authority, runtime, or custody path is introduced.

Canonical user-action surface identity is:

```text
url_route
device_browser_context_class
runtime_surface
action_type
```

Each registered or check-in-scoped surface additionally carries:

```text
surface_id
owner_task_id
request_id optional
sharing = SHAREABLE | EXCLUSIVE
```

The evaluator now compares canonical registered surfaces plus `checkin_context.user_action_surfaces_under_mutation` against other active/check-out task surfaces.

Disposition semantics:

- identical identity with either side `EXCLUSIVE` is an incompatible collision resource;
- if the conflicting owner is currently `CHECKED_OUT`, the existing hard-collision path yields `STOP_COLLISION`;
- otherwise the conflict remains visible in normal collision candidates and yields `COORDINATE_CONVERGENCE`;
- identical `SHAREABLE` + `SHAREABLE` identity is preserved as `SHAREABLE_USER_ACTION_SURFACE / blocking=false`;
- different URL/device-browser/runtime/action identity does not collide merely because it is user-facing.

Registration validation now checks ownership, sharing semantics, required fields, duplicate identities, and canonical schema shape. Focused tests cover exclusive conflict, shareable nonblocking behavior, dynamic check-in ownership, and exact-current/stale/missing/divergent registry-generation handling through both the AI-session gate and the Canonical Work caller surface.

### Related PR / branch reconciliation

- canonical issue `#1343` remains open because this Goal is still `ACTIVE / CHECKED_OUT` and exact-head validation/merge for this final user-action collision slice is pending;
- stale branch `task-registry-action-surface-fence-001` was reconciled to current generation-45 main through merge commit `93c265b59196a6ff1cf744f9581944ceea6ddcd1`; it is the sole active implementation branch for this slice;
- PR `#1760` was closed without merge as obsolete because its target Goal `STEG-BROWSER-RUNTIME-CONSUMPTION-001` is now `RETIRED / DECOMPOSED_AT_PROMPT_LIMIT` with continuation transferred to `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`;
- historical merged task-registry branches/PRs remain audit history and are not active competing claims.

### Validation still required before merge

Require focused source tests and the broad validation lanes available to this repository. Do not promote source implementation to validated/merged until exact-head evidence exists. After validation and before merge, re-read GitHub `main` and the canonical registry generation; if either has advanced, reconcile again before merge.


## Exact-head validation and Master Records evidence review — 2026-09-18

Master Records was reviewed before treating missing CI as a reason to pause. The canonical Master Records work-event custody contract explicitly distinguishes retained/source/CI evidence from authentic runtime execution and requires exact observed evidence to be interpreted according to its class rather than waiting on an absent signal. The relevant evidence trail showed a source-validation problem, not a runtime or custody blocker.

The first Cross-Task Coordination validation run on this slice failed because the task-registration validator compared the PR against stale event field `pull_request.base.sha=3ad023ab...` after current main had advanced. That caused unrelated later task records to be revalidated as if they were part of this PR. The failure was therefore a false change-set expansion, not a failure of the action-surface collision semantics.

The validator was repaired to resolve the synthetic `refs/pull/<n>/merge` commit's first parent directly from the commit object even in a shallow checkout, fetch that exact current base when necessary, and validate only records actually changed by the current PR merge. This preserves fail-closed task registration checks without importing unrelated concurrent main changes.

Exact source-validation evidence at head `74eb777d7e46548dd6fe2faf566782b14c4b1181`:

- Cross-Task Coordination Validation run `35400305724`: PASS, including focused Task Registry collision tests, generation-fence tests, registration validation, and organization-control validation;
- Validate KV AI Memory Resident Binding run `35400305734`: PASS;
- validate-deepseek-resident run `35400305750`: PASS.

Master Records boundary preserved: these runs validate source semantics only. They do not claim runtime execution, authentic custody, WorkerCoordinator claim/fence, Interlock/InTr admission, credential issuance, browser execution, or task completion.


## Goal completion reconciliation — 2026-09-18

PR `#2132` merged as `d92b6cb6bb9ad6c46187161b8796f0405b65e0bf` from exact validated head `521f8fccd2772fe258e8f4d316c0d9648481a1d8`.

Final exact-head validation:

- Cross-Task Coordination Validation `35400627272`: PASS;
- Validate KV AI Memory Resident Binding `35400627268`: PASS;
- validate-deepseek-resident `35400627263`: PASS.

The earlier false failure was traced to stale PR event-base comparison, repaired to use the synthetic merge commit's exact current first parent, and then revalidated cleanly. Master Records review confirmed the correct evidence classification: source/CI evidence validates source semantics but does not claim runtime execution or authentic custody.

All remaining predicates owned by this Goal are now satisfied:

- canonical anti-collision disposition path exists;
- stale/missing/divergent session generation fails closed before mutation;
- Canonical Work and AI-session production callers carry generation context;
- repository/component/lineage/adjacency/substrate overlap remains in the single existing evaluator;
- user-action/runtime-surface identity is first-class;
- exclusive incompatible overlaps stop or coordinate before user instruction/mutation;
- mutually shareable action surfaces remain visible and nonblocking;
- no second collision engine, WorkerCoordinator, Interlock/InTr authority, credential authority, runtime, scheduler, dispatcher, custody plane, or second-device dependency was introduced.

No successor is required for this completed source-coordination goal. Future defects belong to their actual owner unless they expose a genuinely new anti-collision defect.
