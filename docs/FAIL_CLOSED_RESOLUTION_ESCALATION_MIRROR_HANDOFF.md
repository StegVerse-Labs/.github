# Fail-Closed Resolution Escalation Mirror Handoff

## Authority

```text
goal_id: FAIL-CLOSED-RESOLUTION-ESCALATION-001
repository: StegVerse-Labs/.github
branch: feat/fail-closed-resolution-task-escalation-v2
parent_policy: docs/BLOCKER_RESOLUTION_MIRROR_HANDOFF.md
policy_file: control/blocker-resolution-policy.json
runtime: heartbeat_runtime/engine_v10.py
blocker_encoder: heartbeat_runtime/blocker_policy.py
canonical_registry: control/worker-registry.json
state: IMPLEMENTED_PENDING_HOSTED_VALIDATION
```

## Governing invariant

`FAIL_CLOSED` protects the attempted consequence; it does not terminate pursuit of the governing goal.

If a worker reaches a constraint that would otherwise leave the task `BLOCKED`, the worker response must include a resolution contract. The runtime converts that condition into a distinct goal-preserving task in the canonical worker task registry and releases the original worker claim. The originating task moves to `ACTIVATION_PENDING` while the derived task owns resolution work.

A failed resolution task is evidence that its assigned resolution level could not resolve the collision. Unless a same-level retry is explicitly justified by a changed workaround candidate, the runtime escalates to the next level:

```text
WORKER
-> REPOSITORY_OWNER
-> COMPONENT_AUTHORITY
-> ECOSYSTEM_GOVERNANCE
-> HUMAN_AUTHORITY
```

If no admitted worker exists at a machine resolution level, the runtime escalates rather than leaving the task unassigned indefinitely. If no machine level can legally correct the collision, the final task is `HUMAN_AUTHORITY_REQUIRED` and must name the exact correction/decision required.

## Runtime construction

`heartbeat_runtime/blocker_policy.py` validates blocked response contracts and embeds a deterministic `resolution-contract:v1:*` evidence reference into the worker response. This preserves the condition through the existing process-adapter protocol without granting the worker direct registry mutation authority.

`heartbeat_runtime/engine_v10.py` consumes that evidence and:

1. derives a deterministic `RESOLVE-*` or `ESCALATE-*` task ID;
2. writes a schema-compatible generated executable handoff;
3. writes a bounded generated cost basis;
4. appends the derived task to `control/worker-registry.json` in runtime state;
5. releases the original worker claim;
6. changes the original task from `BLOCKED` to `ACTIVATION_PENDING`;
7. admits an eligible resolution worker under the normal fenced heartbeat path;
8. escalates an unresolved resolution task to the next level;
9. reactivates the originating task when its resolution child completes;
10. preserves fail-closed authority throughout the process.

Legacy lifecycle expiry recovery is also normalized: where the older engine creates a distinct `RECOVER-*` task, the expired parent is represented as `ACTIVATION_PENDING` on that active recovery rather than remaining passively `BLOCKED`.

## Constraint contract

Required on every `BLOCKED` worker response:

```text
blocker.dependency_class
blocker.problem_statement
blocker.solution_required=true
blocker.workaround_candidates[]
blocker.next_solution_action
```

Optional but authoritative for escalation:

```text
blocker.trigger_type = FAIL_CLOSED | CONDITIONAL_CONSTRAINT | ...
blocker.resolvable_by_current_worker = true | false
blocker.escalation_target
blocker.required_capabilities[]
blocker.completion_evidence[]
blocker.same_level_retry_authorized
blocker.workaround_candidate_changed
```

A worker may never resolve a collision by silently weakening the originating goal, bypassing StegGate, bypassing a safety predicate, manufacturing credential/route authority, or making GitHub tokens production authority.

## Credential and route boundary

```text
GitHub token production authority: NONE
credential/route authority: TV/TVC
resolution task authority effect: NONE beyond its separately admitted bounded task scope
```

## Validation

Deterministic tests:

```text
python -m unittest tests.test_fail_closed_resolution_escalation
python -m unittest tests.test_blocker_resolution_policy
```

Required assertions include:

- blocked response produces a machine-readable resolution contract;
- blocked worker is converted to a registered resolution task;
- originating worker claim is released rather than parked;
- repeated failure of a derived resolution task escalates a level;
- ecosystem-governance collision escalates to `HUMAN_AUTHORITY` when unresolved;
- fail-closed execution authority remains unchanged.

## Completion / release condition

Source construction is complete on the feature branch. Merge is permitted only after repository validation proves engine v10 compatibility with the existing worker runtime and blocker-policy suites.

After merge, this becomes the canonical runtime rule: passive worker `BLOCKED` is not a stable continuation state when a goal remains unresolved. The registry must contain active solution work or an explicit next-level authority escalation.
