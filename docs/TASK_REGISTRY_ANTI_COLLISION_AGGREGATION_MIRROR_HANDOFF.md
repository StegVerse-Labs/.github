# Task Registry Anti-Collision Aggregation Mirror Handoff

Goal Task ID: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1343`
PR: `StegVerse-Labs/.github#1344`
Status: `ACTIVE / CHECKED_OUT / REGISTRY PREFLIGHT + PORTABLE PRECLAIM ENFORCED / NODE-MANIFOLD REGISTERED / SESSION-TARGET CONTEXT BOUND / EXACT-HEAD VALIDATION PENDING`

## Objective

Every task/session reaching the canonical Task Registry must receive a deterministic pre-mutation disposition derived from current canonical task records, and no portable WorkerCoordinator claim may be minted unless that exact task has a current `CONTINUE` disposition.

## Required dispositions

- `CONTINUE` — no current collision candidate discovered.
- `COORDINATE_CONVERGENCE` — overlapping active work exists; coordinate before mutation.
- `STOP_COLLISION` — a currently checked-out task overlaps the same component or lineage strongly enough that this session should end and continue only through the returned collision owner/convergence path.
- `STOP_SUPERSEDED` — canonical task state is superseded/retired with a continuation task.
- `STOP_INACTIVE` — canonical task is inactive/retired without a continuation.
- `STOP_NOT_REGISTERED` — task is absent from canonical task records and must not mutate source until registered/reconciled.

## Implemented protocol

1. `scripts/evaluate_task_registry_collision_checkin.py` resolves canonical task identity and all active/recently active collision candidates.
2. The evaluator now accepts optional `checkin_context` containing `session_id`, `checked_in_at`, repository, branch, pull request, source head, first unresolved predicate, repositories-under-mutation, and components-under-mutation.
3. Intended mutation targets from that context participate in overlap calculation instead of relying only on static task-record scope.
4. The normalized check-in context and complete disposition are independently SHA-256 bound as `checkin_context_sha256` and `checkin_disposition_sha256`.
5. Canonical Work event bootstrap executes this preflight before route installation or bounded work mutation. Only `CONTINUE` proceeds.
6. Portable current-iPhone WorkerCoordinator checkout requires that same disposition as an explicit third input before it reads or mutates WorkerCoordinator state.
7. Portable checkout validates exact task identity, disposition schema, `authority_effect=NONE`, and `disposition=CONTINUE`; all other states fail closed before claim/fence mutation.
8. WorkerCoordinator claim receipts retain the exact registry disposition hash, preserving the ordering `Task Registry decision -> WorkerCoordinator claim/fence -> Interlock/InTr -> execution` for later reconstruction.

## Canonical files

- `data/canonical-task-records/TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001.json`
- `data/canonical-task-records/STEGOS-NODE-MANIFOLD-001.json`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/install_and_run_canonical_work_event_bootstrap.py`
- `workercoordinator/portable_checkout.js`
- `tests/test_task_registry_collision_checkin.py`
- `tests/test_portable_workercoordinator_registry_gate.py`

## Validation evidence

Initial evaluator head `7b12ca062b463270c7b4564aad502e9a397ea3e8` passed repository suite `34544805866`, organization control `34544805762`, and Heartbeat validation `34544805873`.

Canonical Work ingress head `d7b36d6a6e850e2a423dac62ebf721ca871117fe` passed repository suite `34549352435`, organization control `34549352440`, and Heartbeat validation `34549352456`.

Portable preclaim head `888314d7fd4ed5e301fff360e32581dfb19b8f0f` passed repository suite `34553056822`, organization control `34553056856`, and Heartbeat validation `34553056820`.

Post-Node-Manifold-registration head `479b3e4f14ae85400b21ce35279a22001345aff7` passed repository suite `34553340082`, organization control `34553340116`, and Heartbeat validation `34553340079`.

The branch has advanced with session/branch/PR/intended-target context binding and requires one final exact-head validation before merge.

## Node Manifold visibility repair

`STEGOS-NODE-MANIFOLD-001` is now centrally represented in `.github` canonical task records. Its record points to StegOS issue #23 and the Node Manifold/service-KV handoffs, identifies shared StegOS/.github/Site/KV surfaces, and declares adjacency to global runtime, KV revalidation, Device/KV/SKAP roundtrip, KV-bound browser projection, and Ecosystem Chat work. The task therefore participates in collision aggregation instead of remaining invisible.

## Legacy portable-checkout migration audit

Repository code search found no indexed caller invoking the old `checkout(pkg, store)` contract outside the implementation itself. Existing references point to the portable implementation/package/handoffs but do not expose a second in-repository invocation path. The new fail-closed third argument therefore becomes the enforcement contract; any stale external/current-device caller that still omits the disposition will fail before state mutation rather than bypass collision management.

## README impact review

The root README already defines Task Registry resolution, deduplication, cross-task dependency/collision resolution, and canonical work ingress as prerequisites before autonomous continuation. This change makes that documented ordering fail-closed at Canonical Work and portable WorkerCoordinator preclaim surfaces; it does not create a new authority or runtime. README semantics are therefore judged sufficient for this implementation, with this handoff carrying the exact source-level enforcement details.

## Remaining integration

1. obtain exact-head validation after session-target context binding;
2. if green, merge PR #1344;
3. after merge, persist check-in/check-out event history in a durable coordination event log so recently returned sessions can participate in time-window collision calculations, rather than relying only on the current disposition envelope and WorkerCoordinator receipt lineage;
4. propagate the check-in requirement to any future checkout surface by consuming the same disposition contract rather than implementing another collision engine.

## Authority invariants

Task Registry check-in is coordination evidence only. It grants no claim/fence, execution, credential, transition, custody, publication, release, or completion authority. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Manual work

None.
