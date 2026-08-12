# Fail-Closed Resolution Escalation Mirror Handoff

## Authority

```text
goal_id: FAIL-CLOSED-RESOLUTION-ESCALATION-001
repository: StegVerse-Labs/.github
branch: main
canonical_pr: #82 / MERGED
merge_commit: e0500245085f7dcdabd87c801b5654a619264ca4
parent_policy: docs/BLOCKER_RESOLUTION_MIRROR_HANDOFF.md
broad_state_invariant: control/active-worker-state-policy.json / #83/#84/#85
policy_file: control/blocker-resolution-policy.json
resolution_core: heartbeat_runtime/engine_v10.py
canonical_runtime: heartbeat_runtime/engine_v11.py
blocker_encoder: heartbeat_runtime/blocker_policy.py
canonical_registry: control/worker-registry.json
state: COMPLETE_RELEASED
```

## Governing invariant

`FAIL_CLOSED` protects the attempted consequence; it does not terminate pursuit of the governing goal.

If a worker reaches a fail-closed or conditional constraint that would otherwise leave the task passively stopped, its response must carry a resolution contract. Engine v11 converts that condition into a distinct goal-preserving resolution task, releases the original worker claim, and moves the originating task to `ACTIVATION_PENDING` while the derived task owns solution work.

A failed resolution task is evidence that its assigned resolution level could not resolve the collision. Unless a same-level retry is explicitly justified by changed evidence, escalation proceeds:

```text
WORKER
-> REPOSITORY_OWNER
-> COMPONENT_AUTHORITY
-> ECOSYSTEM_GOVERNANCE
-> HUMAN_AUTHORITY
```

If no admitted worker exists at a machine level, lack of an executor is itself a constraint collision and escalates. If no machine level can legally correct the collision, the final task is `HUMAN_AUTHORITY_REQUIRED` and must preserve the exact unresolved goal/constraints plus the correction or decision required.

## Runtime construction

`heartbeat_runtime/blocker_policy.py` validates worker constraint contracts and embeds a deterministic `resolution-contract:v1:*` evidence reference into the worker response.

`heartbeat_runtime/engine_v10.py` implements deterministic RESOLVE/ESCALATE derivation, generated handoff/cost basis, registry insertion, originating-claim release, parent transition to `ACTIVATION_PENDING`, ordinary fenced worker admission, escalation, and parent reactivation after successful resolution.

`heartbeat_runtime/engine_v11.py` is the canonical compatibility runtime and is exported by `heartbeat_runtime/__init__.py`. The sovereign heartbeat materializer binds engine v11. GitHub Actions, Render, Cloudflare, Vercel, or another hosted service does not become production heartbeat authority through this change.

## Constraint contract

A worker-declared fail-closed/conditional response that cannot complete its attempted action must identify:

```text
blocker.dependency_class
blocker.problem_statement
blocker.solution_required=true
blocker.workaround_candidates[]
blocker.next_solution_action
```

Routing/escalation may additionally identify trigger type, current-worker resolvability, escalation target, required capabilities, completion evidence, same-level retry authorization, and changed workaround evidence.

A worker may never resolve a collision by weakening the originating goal, bypassing StegGate, bypassing a safety predicate, manufacturing credential/route authority, or making GitHub tokens production authority.

## Credential and route boundary

```text
GitHub token production authority: NONE
credential/route authority: TV/TVC
resolution task authority effect: NONE beyond its separately admitted bounded task scope
```

## Validation evidence

Pre-merge and convergence validation established the resolution/escalation mechanics, compatibility runtime, recursive disposable-state materialization, and no-token control-plane behavior. PR #82 merged to main at `e0500245085f7dcdabd87c801b5654a619264ca4`.

Post-merge organization handoff rendering on the merge commit passed (`31620715890`). A stale organization aggregation term check was then corrected to the current physical-resource execution heading; final post-normalization aggregation/control-plane validation is tracked by the organization handoff and issues #83/#84.

## Completion / release condition

Source construction and merge are complete. The canonical runtime rule is now:

```text
failed consequence -> remains fail closed
unsatisfied governing goal -> active registered resolution task
worker cannot resolve constraint collision -> next capable resolution level
automation cannot legally resolve collision -> HUMAN_AUTHORITY_REQUIRED with exact decision/correction request
```

No unresolved worker-declared fail-closed/conditional condition may terminate as passive work. Historical stale registry projections are reconciled separately under the broad state-normalization lane #83/#84 and do not change this released runtime behavior.
