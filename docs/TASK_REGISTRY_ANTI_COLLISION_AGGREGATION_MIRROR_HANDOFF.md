# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
PR: `StegVerse-Labs/.github#1344`
Status: `ACTIVE / CHECKED_OUT / REGISTRY-BOUNDARY DISPOSITION IMPLEMENTED / CANONICAL WORK PREFLIGHT BOUND / PORTABLE WORKERCOORDINATOR PRECLAIM GATE BOUND / NODE-MANIFOLD CENTRAL REGISTRATION ADDED / EXACT-HEAD VALIDATION PENDING`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition derived from current canonical task records, and no WorkerCoordinator claim may be minted from the portable current-iPhone path unless that exact task has a current `CONTINUE` disposition.

## Required dispositions

- `CONTINUE` — no current collision candidate discovered.
- `COORDINATE_CONVERGENCE` — overlapping active work exists; coordinate before mutation.
- `STOP_COLLISION` — a currently checked-out task overlaps the same component or task lineage strongly enough that this session should end and continue only through the returned collision owner/convergence path.
- `STOP_SUPERSEDED` — canonical task state is superseded/retired with a continuation task.
- `STOP_INACTIVE` — canonical task is inactive/retired without a continuation.
- `STOP_NOT_REGISTERED` — task is absent from canonical task records and must not mutate source until registered/reconciled.

## Response requirements

The evaluator returns task ID, canonical handoff when available, disposition, session action, collision candidates, overlapping repositories/components, lineage/adjacency evidence, hard-collision task IDs, continuation task/handoff when applicable, and `authority_effect=NONE`.

## Current implementation

- `data/canonical-task-records/TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001.json`
- `data/canonical-task-records/STEGOS-NODE-MANIFOLD-001.json`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `workercoordinator/portable_checkout.js`
- `tests/test_task_registry_collision_checkin.py`
- `tests/test_portable_workercoordinator_registry_gate.py`

The evaluator reads all canonical task records at check-in time. It does not grant execution authority, replace WorkerCoordinator claims/fences, or treat GitHub as runtime authority.

Canonical Work event bootstrap executes the registry collision preflight before route installation or bounded work bootstrap. Only `CONTINUE` proceeds automatically. `COORDINATE_CONVERGENCE` and every `STOP_*` result fail closed before mutation and surface the complete `TASK_REGISTRY_CHECKIN` JSON to the caller/session. A missing evaluator, malformed response, identity mismatch, or non-NONE authority effect also fails closed before route mutation.

Portable current-iPhone WorkerCoordinator checkout requires that same disposition as an explicit third input before it reads or mutates portable WorkerCoordinator state. The checkout validates schema, exact task identity, `authority_effect=NONE`, and `disposition=CONTINUE`; any other condition fails closed before claim/fence mutation. The emitted WorkerCoordinator checkout receipt includes `registry_checkin_disposition`, `registry_checkin_sha256`, and `registry_checkin_authority_effect`, and the portable state retains the latest registry-checkin hash. This binds claim issuance to the exact non-authorizing Task Registry decision that preceded it without converting the registry into claim authority.

## Validation evidence

PR #1344 head `7b12ca062b463270c7b4564aad502e9a397ea3e8` passed:

- Deterministic Repository Suite - Diagnostic Evidence Only run `34544805866`;
- Validate organization control plane - No GitHub Token Authority run `34544805762`;
- Heartbeat Worker Project - Validation Only / No GitHub Token Authority run `34544805873`.

Canonical Work ingress head `d7b36d6a6e850e2a423dac62ebf721ca871117fe` passed:

- Deterministic Repository Suite run `34549352435`;
- Validate organization control plane run `34549352440`;
- Heartbeat Worker Project validation run `34549352456`.

Portable preclaim gate head `888314d7fd4ed5e301fff360e32581dfb19b8f0f` passed:

- Deterministic Repository Suite run `34553056822`;
- Validate organization control plane run `34553056856`;
- Heartbeat Worker Project validation run `34553056820`.

The branch has advanced again with central `STEGOS-NODE-MANIFOLD-001` registration. Fresh exact-head validation is required before merge.

## Node Manifold visibility repair

The previously invisible active Goal Task `STEGOS-NODE-MANIFOLD-001` is now represented in the central `.github` canonical task records on this branch. Its record points to StegOS issue #23 and the Node Manifold / StegVerse Genesis service-KV handoffs, identifies its shared repositories/components, and marks adjacency to global runtime, KV revalidation, Device/KV/SKAP roundtrip, KV-bound browser projection, and Ecosystem Chat work. This converts the earlier `STOP_NOT_REGISTERED` blind spot into collision-visible registry state without claiming physical network proof or runtime activation.

## Remaining integration

1. obtain fresh exact-head validation after Node Manifold registration and repair any regression;
2. identify any portable checkout caller that still invokes the old two-argument checkout contract and migrate it to supply the exact Task Registry disposition;
3. expose check-in timestamp/session identity/branch-PR target metadata as retained coordination evidence;
4. make task registration/check-in persist enough target information to compute recent-returned collision windows deterministically;
5. add a direct root README reference to the registry preflight and preclaim gate before merge if needed to make the functional change explicit;
6. merge only when required validation remains green.

## Authority invariants

Task Registry check-in is coordination evidence only. It grants no claim/fence, execution, credential, transition, custody, publication, release, or completion authority. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Session handoff note

This session reached its coordination handoff threshold. The next session should begin from `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`, read this handoff first, verify the exact PR #1344 head, and continue from the remaining-integration list rather than reopening already-green enforcement work.

## Manual work

None.
